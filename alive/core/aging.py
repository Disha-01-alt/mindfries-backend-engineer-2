"""Aging assessment — a transparent "biological age" delta.

ALIVE O.S. reports not just a risk score but how a member's physiology compares
to their chronological age. This is a deliberately simple, auditable model: a
few longevity-linked metrics (heart-rate variability, resting heart rate, daily
activity) each nudge an estimated biological age up or down from the member's
real age, and the overall risk score adds a frailty premium.

Pure and deterministic, like everything in ``core`` — it reads only a RiskScore
(itself derived from samples) and a chronological age.
"""

from __future__ import annotations

from dataclasses import dataclass

from .metrics import MetricKind
from .score import RiskScore

# Each longevity metric contributes (years-per-unit-deviation) from its midpoint.
# Negative years = younger than chronological age.
_LONGEVITY = {
    MetricKind.HRV: (-0.08, 80.0),               # higher HRV -> younger
    MetricKind.RESTING_HEART_RATE: (0.15, 60.0),  # higher RHR -> older
    MetricKind.STEPS: (-0.0004, 9500.0),          # more steps -> younger
}
_MAX_DELTA = 15.0  # cap the swing either way, years


@dataclass(frozen=True)
class AgingAssessment:
    member_id: str
    as_of: float
    chronological_age: float
    biological_age: float
    delta_years: float  # biological - chronological; negative is good

    @property
    def is_younger(self) -> bool:
        return self.delta_years < 0


def assess(chronological_age: float, score: RiskScore) -> AgingAssessment:
    delta = 0.0
    agg_by_metric = {c.metric: c.aggregate for c in score.contributions}
    for metric, (per_unit, midpoint) in _LONGEVITY.items():
        agg = agg_by_metric.get(metric)
        if agg is None:
            continue
        delta += per_unit * (agg - midpoint)

    # A frailty premium from overall risk: a high-risk member ages faster.
    delta += score.overall * 0.06

    delta = max(-_MAX_DELTA, min(_MAX_DELTA, delta))
    bio = round(chronological_age + delta, 1)
    return AgingAssessment(
        member_id=score.member_id,
        as_of=score.as_of,
        chronological_age=chronological_age,
        biological_age=bio,
        delta_years=round(delta, 1),
    )
