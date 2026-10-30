"""The processing pipeline: one reading in, through to delivered notifications.

    ingest(reading) -> recompute score -> evaluate alerts -> deliver outbox

``deliver`` drains the outbox and hands each item to the dispatcher. Because a
sweep (or a retry) can re-evaluate a score and re-enqueue the same alert, the
same alert can reach ``deliver`` more than once — at-least-once by design.
"""

from __future__ import annotations

from ..core.metrics import MetricKind
from ..core.score import RiskScore
from ..services.alerting import AlertingService
from ..services.dispatch import Dispatcher
from ..services.ingest import IngestService
from ..services.scoring import ScoringService
from ..store.outbox import Outbox


class Processor:
    def __init__(
        self,
        ingest: IngestService,
        scoring: ScoringService,
        alerting: AlertingService,
        dispatcher: Dispatcher,
        outbox: Outbox,
    ) -> None:
        self._ingest = ingest
        self._scoring = scoring
        self._alerting = alerting
        self._dispatcher = dispatcher
        self._outbox = outbox

    def handle(
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
    ) -> RiskScore | None:
        sample = self._ingest.ingest(
            member_id=member_id,
            device_id=device_id,
            metric=metric,
            event_time=event_time,
            value=value,
            unit=unit,
            seq=seq,
            source=source,
        )
        score = self._scoring.recompute(member_id, triggered_by=sample)
        if score is not None:
            self._alerting.evaluate(score)
        self.deliver()
        return score

    def rescore(self, member_id: str) -> RiskScore | None:
        score = self._scoring.recompute(member_id)
        if score is not None:
            self._alerting.evaluate(score)
        self.deliver()
        return score

    def deliver(self) -> int:
        """Drain the outbox and dispatch each item. Returns the number delivered."""
        delivered = 0
        for item in self._outbox.drain():
            if self._dispatcher.dispatch(item):
                delivered += 1
        return delivered
