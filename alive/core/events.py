"""Derived domain events — alerts and recommendations.

When a score crosses a threshold the engine emits an **Alert** (to a coach, for a
critical reading) or a **Recommendation** / micro-action (to the member). The
one thing that matters for correctness: each carries a **stable id born from the
thing that caused it** — ``stable_id(member, rule, window)`` — not an arrival
counter or a delivery-attempt id. That stable id is what lets dispatch be
idempotent across retries (**B2**): the same rule firing for the same member and
window is the *same* alert, however many times the worker reprocesses it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .ids import stable_id


class Severity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class Recipient(str, Enum):
    MEMBER = "member"
    COACH = "coach"


@dataclass(frozen=True)
class Alert:
    member_id: str
    recipient_id: str      # coach_id or member_id
    recipient_kind: Recipient
    rule: str              # e.g. "critical_risk", "spo2_low"
    severity: Severity
    window: float          # window_start the alert is scoped to
    message: str
    event_time: float      # the watermark that produced it

    @property
    def alert_id(self) -> str:
        # Stable across retries: identity is (member, rule, window), NOT the
        # recipient or the attempt — one rule-firing is one alert.
        return stable_id(self.member_id, self.rule, self.window, prefix="alrt_")

    @property
    def dedup_key(self) -> tuple[str, str]:
        """What at-most-once is keyed on: this recipient + this alert."""
        return (self.recipient_id, self.alert_id)


@dataclass(frozen=True)
class Recommendation:
    member_id: str
    kind: str              # e.g. "move_more", "hydrate", "glucose_checkin"
    message: str
    window: float
    event_time: float

    @property
    def rec_id(self) -> str:
        return stable_id(self.member_id, self.kind, self.window, prefix="rec_")
