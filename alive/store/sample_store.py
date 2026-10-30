"""The sample store — append-only facts.

A reading that happened is a fact: you append it, you never mutate it. Two
integrity rules live here:

  * **Per-(device, metric) monotonic sequence (B6).** Each device numbers its
    readings; the store rejects a sequence that goes backwards (a stale replay
    after a reconnect) with ``SequenceError``. An exact re-send of a frame we
    already have is an idempotent no-op, not an error.
  * **Event time may be out of order.** Monotonic *sequence* is about one
    device's transport; *event time* can still arrive out of order across
    devices (a watch's 9:00 sample landing after a phone's 9:05). That is normal
    and must be stored as-is — reconciling it is scoring's job, not the store's.
"""

from __future__ import annotations

from collections import defaultdict

from ..core.errors import SequenceError
from ..core.metrics import MetricKind
from ..core.sample import Sample


class SampleStore:
    def __init__(self) -> None:
        self._by_member: dict[str, list[Sample]] = defaultdict(list)
        self._by_id: dict[str, Sample] = {}
        self._max_seq: dict[tuple[str, MetricKind], int] = {}

    def append(self, sample: Sample) -> Sample:
        key = (sample.device_id, sample.metric)
        last = self._max_seq.get(key)
        if last is not None:
            if sample.seq < last:
                raise SequenceError(
                    f"sequence went backwards for device {sample.device_id} / {sample.metric.value}: "
                    f"got {sample.seq}, already at {last}"
                )
            if sample.seq == last:
                existing = self._by_id.get(sample.sample_id)
                if existing is not None:
                    return existing  # idempotent re-send of the same frame
                raise SequenceError(
                    f"sequence {sample.seq} reused with different content for "
                    f"device {sample.device_id} / {sample.metric.value}"
                )
        self._max_seq[key] = sample.seq
        self._by_id[sample.sample_id] = sample
        self._by_member[sample.member_id].append(sample)
        return sample

    def for_member(self, member_id: str) -> list[Sample]:
        """All raw samples for a member. Scoring dedupes; the store keeps facts."""
        return list(self._by_member.get(member_id, ()))

    def max_event_time(self, member_id: str) -> float | None:
        """The member's event-time watermark — the newest reading we've observed.

        This is the ``as_of`` a correct score is computed for: it never goes
        backwards when a late, older-event-time sample arrives.
        """
        samples = self._by_member.get(member_id)
        if not samples:
            return None
        return max(s.event_time for s in samples)

    def members(self) -> list[str]:
        return [m for m, s in self._by_member.items() if s]

    def count(self) -> int:
        return len(self._by_id)
