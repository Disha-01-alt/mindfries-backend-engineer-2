"""A Sample — one biometric reading, in canonical units, with its provenance.

Modelled on Open mHealth's ``DataPoint{header, body}`` split: the *body* is the
measurement (metric, value, unit); the *header* is provenance (which member,
which device, which source synced it, when it happened on the device, and a
per-device sequence number). Everything the engine ever stores or scores is a
Sample — a wearable reading, a lab result (``source="lab"``), and a daily
check-in (``source="checkin"``) are all Samples with different sources, so one
model and one pipeline serve all three ingestion paths.

A Sample is **frozen and canonical**: by the time one exists its value has
already been normalized to the metric's canonical unit (``units.normalize``), so
nothing downstream re-interprets units.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .ids import stable_id
from .metrics import MetricKind


@dataclass(frozen=True)
class Sample:
    member_id: str
    device_id: str
    metric: MetricKind
    event_time: float  # epoch seconds — when the reading happened on the device
    value: float       # in the metric's canonical unit
    unit: str          # the canonical unit (kept for display/audit)
    seq: int           # per (device, metric) monotonic sequence number
    source: str        # provenance: goqii_band | apple_health | lab | checkin | manual
    ingested_at: Optional[float] = None  # processing time; set by the ingest service

    @property
    def sample_id(self) -> str:
        """Stable, content-derived id — identical across re-syncs of this reading."""
        return stable_id(self.member_id, self.device_id, self.metric.value, self.event_time, self.seq, prefix="smp_")

    @property
    def identity_key(self) -> tuple[str, MetricKind, float]:
        """Logical identity for cross-source dedup (B3).

        The same physiological reading synced from two apps (phone + watch) is
        the same ``(member, metric, instant)`` even though the device_id and
        source differ. Event time is rounded to the millisecond so float noise
        from re-serialization doesn't split one reading into two.
        """
        return (self.member_id, self.metric, round(self.event_time, 3))

    def with_ingested_at(self, t: float) -> "Sample":
        return Sample(
            member_id=self.member_id,
            device_id=self.device_id,
            metric=self.metric,
            event_time=self.event_time,
            value=self.value,
            unit=self.unit,
            seq=self.seq,
            source=self.source,
            ingested_at=t,
        )
