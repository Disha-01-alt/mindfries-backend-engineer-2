"""The Engine — ALIVE O.S.'s composition root.

Wires the in-memory stores, the services, and the worker into one object and
exposes the handful of use cases the API and tests drive: enroll a member,
register a device, submit a reading (which scores, alerts, and dispatches), read
a score with its lineage, read an aging assessment, and roll a cohort up.

Construct with a ``ManualClock`` in tests to make every time a controllable
input; production uses the default ``SystemClock``.
"""

from __future__ import annotations

from .core.aging import AgingAssessment, assess
from .core.clock import Clock, SystemClock
from .core.metrics import MetricKind
from .core.score import RiskScore
from .services.alerting import AlertingService
from .services.cohorts import CohortService, CohortSummary
from .services.coaching import CoachingService
from .services.dispatch import Dispatcher
from .services.ingest import IngestService
from .services.scoring import ScoringService
from .store.dispatch_log import DispatchLog
from .store.member_store import Device, Member, MemberStore
from .store.outbox import Item, Outbox
from .store.sample_store import SampleStore
from .store.score_store import ScoreStore
from .worker.processor import Processor
from .worker.scheduler import Scheduler

DEFAULT_COACHES = ["coach_asha", "coach_ravi", "coach_meera"]


class Engine:
    def __init__(self, clock: Clock | None = None, coaches: list[str] | None = None) -> None:
        self.clock: Clock = clock or SystemClock()

        # stores
        self.members = MemberStore()
        self.samples = SampleStore()
        self.scores = ScoreStore()
        self.dispatch_log = DispatchLog()
        self.outbox = Outbox()

        # services
        self.ingest = IngestService(self.members, self.samples, self.clock)
        self.scoring = ScoringService(self.samples, self.scores)
        self.alerting = AlertingService(self.members, self.outbox)
        self.dispatcher = Dispatcher(self.dispatch_log)
        self.coaching = CoachingService(self.members, coaches or DEFAULT_COACHES)
        self.cohorts = CohortService(self.scores)

        # worker
        self.processor = Processor(self.ingest, self.scoring, self.alerting, self.dispatcher, self.outbox)
        self.scheduler = Scheduler(self.processor, self.members, self.clock)

    # ── enrollment ────────────────────────────────────────────────────────────
    def enroll(self, member_id: str, name: str, chronological_age: float, coach_id: str | None = None) -> Member:
        member = self.members.enroll(Member(member_id=member_id, name=name, chronological_age=chronological_age, enrolled_at=self.clock.now()))
        if coach_id:
            self.members.assign_coach(member_id, coach_id)
        else:
            self.coaching.assign_next(member_id)
        return member

    def register_device(self, device_id: str, member_id: str, source: str, kind: str) -> Device:
        return self.members.register_device(Device(device_id=device_id, member_id=member_id, source=source, kind=kind))

    # ── ingestion / scoring ────────────────────────────────────────────────────
    def submit(
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
        return self.processor.handle(
            member_id=member_id, device_id=device_id, metric=metric, event_time=event_time,
            value=value, unit=unit, seq=seq, source=source,
        )

    def score_of(self, member_id: str) -> RiskScore | None:
        return self.scores.get(member_id)

    def aging_of(self, member_id: str) -> AgingAssessment | None:
        score = self.scores.get(member_id)
        if score is None or not score.has_data:
            return None
        member = self.members.get_member(member_id)
        return assess(member.chronological_age, score)

    # ── delivery / cohorts / sweeps ─────────────────────────────────────────────
    @property
    def deliveries(self) -> list[Item]:
        return self.dispatcher.deliveries

    def cohort_summary(self, member_ids: list[str]) -> CohortSummary:
        return self.cohorts.summary(member_ids)

    def sweep(self) -> int:
        return self.scheduler.sweep()
