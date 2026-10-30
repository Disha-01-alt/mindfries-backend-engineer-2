"""Alerting — turn a score into alerts (to coaches) and recommendations (to
members), and enqueue them on the outbox for the worker to deliver.

Each derived event gets a stable id from ``(member, rule, window)`` (see
``core/events.py``), so re-evaluating the same score, or the worker reprocessing
the outbox, produces the *same* alert — the precondition for idempotent dispatch.
"""

from __future__ import annotations

from ..core.events import Alert, Recipient, Recommendation, Severity
from ..core.metrics import MetricKind
from ..core.score import RiskBand, RiskScore
from ..core.windows import DAY, window_start
from ..store.member_store import MemberStore
from ..store.outbox import Item, Outbox
from . import recommendations

# A metric whose risk exceeds this escalates to a coach alert, not just a nudge.
_COACH_METRIC_THRESHOLD = 60.0
_CRITICAL_METRICS = {MetricKind.SPO2, MetricKind.BLOOD_GLUCOSE, MetricKind.SYSTOLIC_BP}


class AlertingService:
    def __init__(self, members: MemberStore, outbox: Outbox) -> None:
        self._members = members
        self._outbox = outbox

    def evaluate(self, score: RiskScore) -> list[Item]:
        if not score.has_data:
            return []
        window = window_start(score.as_of, DAY)
        member = self._members.get_member(score.member_id)
        coach = member.coach_id or member.member_id  # self-coached falls back to the member
        items: list[Item] = []

        # Overall-band escalation to the coach.
        if score.band in (RiskBand.HIGH, RiskBand.CRITICAL):
            sev = Severity.CRITICAL if score.band is RiskBand.CRITICAL else Severity.WARNING
            items.append(
                Alert(
                    member_id=score.member_id,
                    recipient_id=coach,
                    recipient_kind=Recipient.COACH,
                    rule="overall_" + score.band.value,
                    severity=sev,
                    window=window,
                    message=f"{member.name}'s risk is {score.band.value} ({score.overall}).",
                    event_time=score.as_of,
                )
            )

        # Specific critical-metric breaches also escalate.
        for c in score.contributions:
            if c.metric in _CRITICAL_METRICS and c.risk >= _COACH_METRIC_THRESHOLD:
                items.append(
                    Alert(
                        member_id=score.member_id,
                        recipient_id=coach,
                        recipient_kind=Recipient.COACH,
                        rule=f"{c.metric.value}_breach",
                        severity=Severity.CRITICAL,
                        window=window,
                        message=f"{member.name}: {c.note}",
                        event_time=score.as_of,
                    )
                )

        # Member-facing micro-actions.
        items.extend(recommendations.build(score))

        for item in items:
            self._outbox.enqueue(item)
        return items
