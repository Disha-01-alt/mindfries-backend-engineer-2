"""Recommendations — the member-facing micro-actions derived from a score.

Pure: a function of the score's lineage. Each metric that carries real risk maps
to one concrete, actionable nudge (ALIVE O.S. dispatches "micro-actions", not raw
numbers). The window on each recommendation is the score's window, so the
recommendation gets a stable id and dedupes like an alert.
"""

from __future__ import annotations

from ..core.events import Recommendation
from ..core.metrics import MetricKind
from ..core.score import RiskScore
from ..core.windows import DAY, window_start

# metric -> (recommendation kind, message), fired when that metric's risk is high.
_RULES: dict[MetricKind, tuple[str, str]] = {
    MetricKind.STEPS: ("move_more", "Your activity is below target — aim for a 20-minute walk today."),
    MetricKind.SLEEP: ("sleep_hygiene", "Your sleep is off your healthy range — try a consistent wind-down tonight."),
    MetricKind.BLOOD_GLUCOSE: ("glucose_checkin", "Your glucose readings are trending out of range — log a check-in with your coach."),
    MetricKind.HRV: ("recovery", "Low heart-rate variability suggests you need recovery — keep today easy."),
    MetricKind.SPO2: ("breathing", "Your blood-oxygen readings are low — try a guided breathing session and consult if it persists."),
    MetricKind.RESTING_HEART_RATE: ("rest", "Your resting heart rate is elevated — prioritise rest and hydration."),
}
_RISK_THRESHOLD = 30.0


def build(score: RiskScore) -> list[Recommendation]:
    window = window_start(score.as_of, DAY)
    out: list[Recommendation] = []
    for c in score.contributions:
        rule = _RULES.get(c.metric)
        if rule and c.risk >= _RISK_THRESHOLD:
            kind, message = rule
            out.append(Recommendation(member_id=score.member_id, kind=kind, message=message, window=window, event_time=score.as_of))
    return out
