"""The score store — a member's current risk score.

A plain latest-view keyed by member. It deliberately stores whatever score it's
given: the *as-of correctness* of that score (that it reflects the newest
event-time data and never regresses) is enforced upstream, by the scoring
service computing the score ``as_of`` the member's event-time watermark. Keeping
the store dumb keeps the single source of truth for the invariant in one place
(``services/scoring.py``).

``history`` keeps the sequence of scores written for a member — not needed for
serving, but it makes the as-of behaviour observable in tests and in an audit.
"""

from __future__ import annotations

from collections import defaultdict

from ..core.score import RiskScore


class ScoreStore:
    def __init__(self) -> None:
        self._current: dict[str, RiskScore] = {}
        self._history: dict[str, list[RiskScore]] = defaultdict(list)

    def put(self, score: RiskScore) -> RiskScore:
        self._current[score.member_id] = score
        self._history[score.member_id].append(score)
        return score

    def get(self, member_id: str) -> RiskScore | None:
        return self._current.get(member_id)

    def history(self, member_id: str) -> list[RiskScore]:
        return list(self._history.get(member_id, ()))

    def all(self) -> list[RiskScore]:
        return list(self._current.values())
