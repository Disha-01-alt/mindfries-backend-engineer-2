"""Shared test fixtures: a fresh engine on a manual clock, and sample builders."""

from __future__ import annotations

from alive.core.clock import ManualClock
from alive.core.metrics import MetricKind, canonical_unit
from alive.core.sample import Sample
from alive.core.windows import DAY
from alive.engine import Engine

BASE = DAY * 10000  # a fixed epoch day so every event time is reproducible

UNITS = {
    MetricKind.RESTING_HEART_RATE: "bpm",
    MetricKind.HEART_RATE: "bpm",
    MetricKind.HRV: "ms",
    MetricKind.STEPS: "count",
    MetricKind.SLEEP: "min",
    MetricKind.SPO2: "%",
    MetricKind.BLOOD_GLUCOSE: "mg/dL",
    MetricKind.SYSTOLIC_BP: "mmHg",
    MetricKind.DIASTOLIC_BP: "mmHg",
    MetricKind.BODY_WEIGHT: "kg",
    MetricKind.BODY_TEMP: "degC",
    MetricKind.ACTIVE_ENERGY: "kcal",
}


def fresh_engine(start: float = BASE) -> Engine:
    return Engine(clock=ManualClock(start=start))


def enrolled(engine: Engine, member_id: str = "m1", age: float = 40, coach: str = "coach_asha") -> str:
    engine.enroll(member_id, f"Test {member_id}", age, coach)
    engine.register_device(f"{member_id}_band", member_id, "goqii_band", "band")
    engine.register_device(f"{member_id}_phone", member_id, "apple_health", "phone")
    return member_id


def make_sample(
    metric: MetricKind,
    event_time: float,
    value: float,
    seq: int,
    member_id: str = "m1",
    device_id: str | None = None,
    source: str = "goqii_band",
) -> Sample:
    """A canonical Sample built directly (for core/store tests that bypass ingest)."""
    return Sample(
        member_id=member_id,
        device_id=device_id or f"{member_id}_band",
        metric=metric,
        event_time=event_time,
        value=float(value),
        unit=canonical_unit(metric),
        seq=seq,
        source=source,
    )
