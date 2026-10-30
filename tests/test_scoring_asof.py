"""The as-of monotonicity invariant (B1) — the heart of the engine.

A member's score must always reflect their newest event-time reading; a late,
older-event-time sample is folded into history but never regresses the score's
``as_of`` to stale data.
"""

import unittest

from alive.core.metrics import MetricKind
from alive.services.scoring import ScoringService
from alive.store.sample_store import SampleStore
from alive.store.score_store import ScoreStore
from tests.helpers import BASE, make_sample


class TestAsOf(unittest.TestCase):
    def setUp(self):
        self.samples = SampleStore()
        self.scores = ScoreStore()
        self.scoring = ScoringService(self.samples, self.scores)

    def _ingest_and_score(self, sample):
        self.samples.append(sample)
        return self.scoring.recompute(sample.member_id, triggered_by=sample)

    def test_score_as_of_tracks_the_latest_event_time(self):
        self._ingest_and_score(make_sample(MetricKind.STEPS, BASE, 3000, 1))
        s = self._ingest_and_score(make_sample(MetricKind.STEPS, BASE + 3600, 3200, 2))
        self.assertEqual(s.as_of, BASE + 3600)

    def test_late_sample_does_not_regress_as_of(self):
        # Newest reading first, then a late one with an OLDER event time.
        self._ingest_and_score(make_sample(MetricKind.STEPS, BASE + 3600, 3200, 1, device_id="m1_band"))
        before = self.scores.get("m1")
        after = self._ingest_and_score(
            make_sample(MetricKind.STEPS, BASE, 9000, 1, device_id="m1_phone", source="apple_health")
        )
        self.assertEqual(after.as_of, before.as_of)       # did NOT go backwards
        self.assertEqual(after.as_of, BASE + 3600)

    def test_late_sample_is_still_folded_into_history(self):
        # The late reading must still affect the score (it's real data), just
        # without moving the watermark back.
        self._ingest_and_score(make_sample(MetricKind.RESTING_HEART_RATE, BASE + 3600, 90, 1, device_id="m1_band"))
        high = self.scores.get("m1").overall
        # A late, good resting-HR reading from a second device lowers the average.
        self._ingest_and_score(
            make_sample(MetricKind.RESTING_HEART_RATE, BASE, 55, 1, device_id="m1_phone", source="apple_health")
        )
        folded = self.scores.get("m1")
        self.assertEqual(folded.as_of, BASE + 3600)       # watermark held
        self.assertLess(folded.overall, high)             # but the late reading counted

    def test_recompute_is_order_independent(self):
        # Ingesting the same facts in two different orders yields the same score.
        order_a = [
            make_sample(MetricKind.STEPS, BASE, 2000, 1),
            make_sample(MetricKind.STEPS, BASE + 3600, 2500, 2),
            make_sample(MetricKind.HRV, BASE + 100, 40, 3),
        ]
        for s in order_a:
            self._ingest_and_score(s)
        a = self.scores.get("m1")

        # Fresh engine, reverse order (seqs renumbered so the store accepts them).
        self.samples = SampleStore()
        self.scores = ScoreStore()
        self.scoring = ScoringService(self.samples, self.scores)
        reordered = [
            make_sample(MetricKind.HRV, BASE + 100, 40, 1, device_id="d2"),
            make_sample(MetricKind.STEPS, BASE + 3600, 2500, 2, device_id="d2"),
            make_sample(MetricKind.STEPS, BASE, 2000, 3, device_id="d2"),
        ]
        for s in reordered:
            self._ingest_and_score(s)
        b = self.scores.get("m1")

        self.assertEqual(a.as_of, b.as_of)
        self.assertEqual(a.overall, b.overall)
        self.assertEqual(a.band, b.band)

    def test_no_samples_no_score(self):
        self.assertIsNone(self.scoring.recompute("ghost"))


if __name__ == "__main__":
    unittest.main()
