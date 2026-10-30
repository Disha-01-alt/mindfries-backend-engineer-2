"""The metric registry: every biometric the engine understands, its canonical
unit, its healthy range, and how it aggregates over a window and bends the risk
score.

Keeping this as data (not scattered ``if metric == ...`` branches) is the Open
mHealth lesson — a measurement's unit and meaning are a *schema property*, so
normalization and scoring are table lookups, and adding a metric is a one-line
registry entry rather than edits across the engine.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class MetricKind(str, Enum):
    RESTING_HEART_RATE = "resting_heart_rate"
    HEART_RATE = "heart_rate"
    HRV = "hrv"
    STEPS = "steps"
    SLEEP = "sleep"
    SPO2 = "spo2"
    BLOOD_GLUCOSE = "blood_glucose"
    SYSTOLIC_BP = "systolic_bp"
    DIASTOLIC_BP = "diastolic_bp"
    BODY_WEIGHT = "body_weight"
    BODY_TEMP = "body_temp"
    ACTIVE_ENERGY = "active_energy"


class Direction(str, Enum):
    HIGHER_BETTER = "higher_better"
    LOWER_BETTER = "lower_better"
    IN_RANGE = "in_range"


class Aggregation(str, Enum):
    MEAN = "mean"
    SUM = "sum"
    LATEST = "latest"
    MIN = "min"
    MAX = "max"


@dataclass(frozen=True)
class MetricSpec:
    kind: MetricKind
    canonical_unit: str
    healthy_low: float
    healthy_high: float
    direction: Direction
    aggregation: Aggregation
    # How much this metric can move the overall risk score, 0..1 relative weight.
    weight: float

    def __post_init__(self) -> None:
        if self.healthy_low > self.healthy_high:
            raise ValueError(f"{self.kind}: healthy_low > healthy_high")
        if self.weight <= 0:
            raise ValueError(f"{self.kind}: weight must be positive")


# The registry. Ranges are deliberately conventional adult references — the point
# of the assessment is the engineering around the score, not clinical calibration.
_REGISTRY: dict[MetricKind, MetricSpec] = {
    s.kind: s
    for s in [
        MetricSpec(MetricKind.RESTING_HEART_RATE, "bpm", 50, 70, Direction.LOWER_BETTER, Aggregation.MEAN, 1.2),
        MetricSpec(MetricKind.HEART_RATE, "bpm", 55, 95, Direction.IN_RANGE, Aggregation.MEAN, 0.5),
        MetricSpec(MetricKind.HRV, "ms", 40, 120, Direction.HIGHER_BETTER, Aggregation.MEAN, 1.1),
        MetricSpec(MetricKind.STEPS, "count", 7000, 12000, Direction.HIGHER_BETTER, Aggregation.SUM, 1.0),
        MetricSpec(MetricKind.SLEEP, "min", 420, 540, Direction.IN_RANGE, Aggregation.SUM, 1.0),
        MetricSpec(MetricKind.SPO2, "pct", 95, 100, Direction.HIGHER_BETTER, Aggregation.MEAN, 1.3),
        MetricSpec(MetricKind.BLOOD_GLUCOSE, "mg/dL", 70, 110, Direction.IN_RANGE, Aggregation.MEAN, 1.4),
        MetricSpec(MetricKind.SYSTOLIC_BP, "mmHg", 90, 125, Direction.IN_RANGE, Aggregation.MEAN, 1.3),
        MetricSpec(MetricKind.DIASTOLIC_BP, "mmHg", 60, 82, Direction.IN_RANGE, Aggregation.MEAN, 1.1),
        MetricSpec(MetricKind.BODY_WEIGHT, "kg", 45, 95, Direction.IN_RANGE, Aggregation.LATEST, 0.4),
        MetricSpec(MetricKind.BODY_TEMP, "degC", 36.1, 37.5, Direction.IN_RANGE, Aggregation.MEAN, 0.6),
        MetricSpec(MetricKind.ACTIVE_ENERGY, "kcal", 300, 900, Direction.HIGHER_BETTER, Aggregation.SUM, 0.8),
    ]
}


def spec_for(kind: MetricKind) -> MetricSpec:
    try:
        return _REGISTRY[kind]
    except KeyError:
        raise KeyError(f"unknown metric: {kind!r}") from None


def all_specs() -> list[MetricSpec]:
    return list(_REGISTRY.values())


def canonical_unit(kind: MetricKind) -> str:
    return spec_for(kind).canonical_unit
