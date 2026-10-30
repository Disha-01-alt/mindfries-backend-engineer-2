"""Cohorts — population aggregation for enterprise partners.

GoQii's B2B customers (corporate employers, insurers) see their population's
health in aggregate, never one member's raw readings. This service rolls the
per-member scores up into a cohort summary: the band distribution, the average
risk, and which members are high-risk enough to prioritise — all derived from the
same score store that serves individuals, so the aggregate can never disagree
with the detail.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..core.score import RiskBand
from ..store.score_store import ScoreStore


@dataclass(frozen=True)
class CohortSummary:
    size: int                               # members in the cohort
    scored: int                             # how many have a score yet
    average_overall: float                  # mean risk over scored members
    band_distribution: dict[str, int] = field(default_factory=dict)
    high_risk_members: tuple[str, ...] = ()  # HIGH or CRITICAL, worst first


class CohortService:
    def __init__(self, scores: ScoreStore) -> None:
        self._scores = scores

    def summary(self, member_ids: list[str]) -> CohortSummary:
        bands = {b.value: 0 for b in RiskBand}
        scored = []
        for mid in member_ids:
            s = self._scores.get(mid)
            if s is None or not s.has_data:
                continue
            scored.append(s)
            bands[s.band.value] += 1

        avg = round(sum(s.overall for s in scored) / len(scored), 2) if scored else 0.0
        high = sorted(
            (s for s in scored if s.band in (RiskBand.HIGH, RiskBand.CRITICAL)),
            key=lambda s: s.overall,
            reverse=True,
        )
        return CohortSummary(
            size=len(member_ids),
            scored=len(scored),
            average_overall=avg,
            band_distribution=bands,
            high_risk_members=tuple(s.member_id for s in high),
        )
