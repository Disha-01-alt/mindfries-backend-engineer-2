"""Cross-source deduplication (**B3**).

One real reading often arrives more than once: a watch and a phone both sync the
same 7:00am resting heart rate, or a direct band feed overlaps a Health-Connect
mirror. They share a logical identity (``Sample.identity_key`` — member, metric,
instant) but differ in ``device_id``/``source``. Counting both would move a
score for a non-reason.

The rule is **priority-based, like Health Connect's aggregate()**: for a given
logical identity, the highest-priority source wins; ties break deterministically
(sequence, then value) so dedup never depends on arrival order.
"""

from __future__ import annotations

from typing import Iterable

from .sample import Sample

# Lower number = higher priority. A clinical lab beats a medical-grade band,
# which beats a phone's aggregated mirror, which beats a self-reported check-in.
_PRIORITY = {
    "lab": 0,
    "goqii_band": 1,
    "apple_health": 2,
    "health_connect": 2,
    "manual": 3,
    "checkin": 4,
}
_DEFAULT_PRIORITY = 5


def source_priority(source: str) -> int:
    return _PRIORITY.get(source, _DEFAULT_PRIORITY)


def prefer(a: Sample, b: Sample) -> Sample:
    """Which of two same-identity samples to keep. Deterministic and total."""
    ka = (source_priority(a.source), -a.seq, -a.value)
    kb = (source_priority(b.source), -b.seq, -b.value)
    return a if ka <= kb else b


def dedupe(samples: Iterable[Sample]) -> list[Sample]:
    """Collapse same-identity samples, keeping the preferred one.

    Output is sorted by ``(event_time, metric)`` so the result is a stable,
    arrival-order-independent canonical view of the readings.
    """
    best: dict[tuple, Sample] = {}
    for s in samples:
        key = s.identity_key
        cur = best.get(key)
        best[key] = s if cur is None else prefer(cur, s)
    return sorted(best.values(), key=lambda s: (s.event_time, s.metric.value))
