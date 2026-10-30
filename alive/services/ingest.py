"""Ingestion — normalize at the edge, then append.

Every reading (wearable, lab, check-in) enters here. The service:

  1. checks the member is enrolled and the device registered (provenance),
  2. normalizes the value to the metric's canonical unit (rejecting a unit it
     can't convert — a glucose reading in the wrong unit must never be scored),
  3. stamps processing time from the injected clock,
  4. appends to the sample store, which enforces the per-device monotonic
     sequence.

What it does *not* do is decide "is this the newest reading?" — event time can
arrive out of order, and reconciling that is scoring's job. Ingestion just
records the fact.
"""

from __future__ import annotations

from ..core.clock import Clock
from ..core.errors import EnrollmentError
from ..core.metrics import MetricKind
from ..core.sample import Sample
from ..core.units import normalize
from ..store.member_store import MemberStore
from ..store.sample_store import SampleStore


class IngestService:
    def __init__(self, members: MemberStore, samples: SampleStore, clock: Clock) -> None:
        self._members = members
        self._samples = samples
        self._clock = clock

    def ingest(
        self,
        *,
        member_id: str,
        device_id: str,
        metric: MetricKind,
        event_time: float,
        value: float,
        unit: str,
        seq: int,
        source: str,
    ) -> Sample:
        if not self._members.is_enrolled(member_id):
            raise EnrollmentError(f"member {member_id} is not enrolled")
        if not self._members.has_device(device_id):
            raise EnrollmentError(f"device {device_id} is not registered")
        device = self._members.get_device(device_id)
        if device.member_id != member_id:
            raise EnrollmentError(f"device {device_id} belongs to a different member")

        canonical_value = normalize(metric, value, unit)
        from ..core.metrics import canonical_unit

        sample = Sample(
            member_id=member_id,
            device_id=device_id,
            metric=metric,
            event_time=event_time,
            value=canonical_value,
            unit=canonical_unit(metric),
            seq=seq,
            source=source,
        ).with_ingested_at(self._clock.now())
        return self._samples.append(sample)
