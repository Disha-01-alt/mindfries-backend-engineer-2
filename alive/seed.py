"""Deterministic seed data — a small, realistic population.

Three members with contrasting physiology (a fit member, a drifting one, and a
high-risk one), each with a band and a phone, and a week of daily readings. No
randomness: the same seed call always produces the same samples and therefore
the same scores, so a demo, a test, and the API all agree.
"""

from __future__ import annotations

from .core.metrics import MetricKind
from .core.windows import DAY
from .engine import Engine

# A fixed anchor so event times are stable and reproducible.
ANCHOR = DAY * 20000  # an arbitrary but fixed epoch day

# member_id -> (name, age, per-metric daily value). Values chosen to land each
# member in a distinct risk band.
_POP = {
    "m_fit": {
        "name": "Asha Rao",
        "age": 34,
        "metrics": {
            MetricKind.RESTING_HEART_RATE: 58,
            MetricKind.HRV: 95,
            MetricKind.STEPS: 11000,
            MetricKind.SLEEP: 470,
            MetricKind.SPO2: 98,
            MetricKind.BLOOD_GLUCOSE: 92,
            MetricKind.SYSTOLIC_BP: 116,
            MetricKind.DIASTOLIC_BP: 74,
        },
    },
    "m_drift": {
        "name": "Ravi Menon",
        "age": 47,
        "metrics": {
            MetricKind.RESTING_HEART_RATE: 72,
            MetricKind.HRV: 55,
            MetricKind.STEPS: 6200,
            MetricKind.SLEEP: 390,
            MetricKind.SPO2: 96,
            MetricKind.BLOOD_GLUCOSE: 118,
            MetricKind.SYSTOLIC_BP: 128,
            MetricKind.DIASTOLIC_BP: 84,
        },
    },
    "m_risk": {
        "name": "Meera Iyer",
        "age": 58,
        "metrics": {
            MetricKind.RESTING_HEART_RATE: 86,
            MetricKind.HRV: 32,
            MetricKind.STEPS: 2600,
            MetricKind.SLEEP: 340,
            MetricKind.SPO2: 91,
            MetricKind.BLOOD_GLUCOSE: 165,
            MetricKind.SYSTOLIC_BP: 146,
            MetricKind.DIASTOLIC_BP: 94,
        },
    },
}

_UNITS = {
    MetricKind.RESTING_HEART_RATE: "bpm",
    MetricKind.HRV: "ms",
    MetricKind.STEPS: "count",
    MetricKind.SLEEP: "min",
    MetricKind.SPO2: "%",
    MetricKind.BLOOD_GLUCOSE: "mg/dL",
    MetricKind.SYSTOLIC_BP: "mmHg",
    MetricKind.DIASTOLIC_BP: "mmHg",
}


def seed(engine: Engine, days: int = 7) -> list[str]:
    """Populate ``engine`` with the seed population. Returns the member ids."""
    ids = []
    for member_id, spec in _POP.items():
        ids.append(member_id)
        engine.enroll(member_id, spec["name"], spec["age"])
        band = f"{member_id}_band"
        engine.register_device(band, member_id, "goqii_band", "band")
        seq = 0
        for day in range(days):
            day_start = ANCHOR + day * DAY
            for metric, value in spec["metrics"].items():
                seq += 1
                engine.submit(
                    member_id=member_id,
                    device_id=band,
                    metric=metric,
                    event_time=day_start + 9 * 3600,  # 9am reading
                    value=float(value),
                    unit=_UNITS[metric],
                    seq=seq,
                    source="goqii_band",
                )
    return ids
