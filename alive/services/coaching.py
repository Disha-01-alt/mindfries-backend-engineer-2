"""Coaching — assign members to human coaches and report coach load.

Deliberately small: coaches are assigned round-robin among the active roster so
load stays even and the assignment is deterministic (no randomness). Alerts for a
member route to that member's coach (see ``alerting.py``).
"""

from __future__ import annotations

from ..core.errors import ValidationError
from ..store.member_store import MemberStore


class CoachingService:
    def __init__(self, members: MemberStore, roster: list[str]) -> None:
        if not roster:
            raise ValidationError("a coaching roster needs at least one coach")
        self._members = members
        self._roster = list(roster)
        self._cursor = 0

    def assign_next(self, member_id: str) -> str:
        coach = self._roster[self._cursor % len(self._roster)]
        self._cursor += 1
        self._members.assign_coach(member_id, coach)
        return coach

    def load(self) -> dict[str, int]:
        counts = {c: 0 for c in self._roster}
        for m in self._members.members():
            if m.coach_id in counts:
                counts[m.coach_id] += 1
        return counts

    def members_of(self, coach_id: str) -> list[str]:
        return [m.member_id for m in self._members.members() if m.coach_id == coach_id]
