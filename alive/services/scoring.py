"""Scoring — recompute a member's risk score, honestly as-of their newest data.

This is the one place the **as-of monotonicity invariant (B1)** is enforced:

    A member's score always reflects the newest event-time reading observed for
    them. A late, older-event-time sample is folded into history but never
    regresses the score below what newer data already established.

The mechanism is a single decision — *what watermark do we score as of?* The
answer must be the member's **maximum event time across all their samples**, not
the event time of whichever reading happened to trigger this recompute. Because
readings arrive out of order (a watch's 9:00 sample landing after a phone's
9:05), scoring "as of the reading we just got" would regress the score to stale
data every time a late one shows up.

Since the recompute runs over *all* the member's samples up to that watermark,
it is also order-independent (``core.score.compute`` is pure), so re-running
after a late arrival folds the late reading into history without moving ``as_of``
backwards.
"""

from __future__ import annotations

from ..core.sample import Sample
from ..core.score import RiskScore, compute
from ..store.sample_store import SampleStore
from ..store.score_store import ScoreStore


class ScoringService:
    def __init__(self, samples: SampleStore, scores: ScoreStore) -> None:
        self._samples = samples
        self._scores = scores

    def recompute(self, member_id: str, triggered_by: Sample | None = None) -> RiskScore | None:
        """Recompute and store ``member_id``'s score. Returns None if no data.

        ``triggered_by`` is the reading that prompted this recompute; it is
        informational only. The watermark is deliberately the member's newest
        event time, NOT the trigger's — see the module docstring (B1).
        """
        watermark = self._samples.max_event_time(member_id)
        if watermark is None:
            return None
        samples = self._samples.for_member(member_id)
        score = compute(member_id, samples, as_of=watermark)
        return self._scores.put(score)
