import unittest

from alive.core.metrics import MetricKind
from alive.core.windows import DAY
from alive.seed import seed
from tests.helpers import BASE, enrolled, fresh_engine


class TestEngineIntegration(unittest.TestCase):
    def test_end_to_end_flow(self):
        e = fresh_engine()
        enrolled(e, "m1", age=45)
        e.submit(member_id="m1", device_id="m1_band", metric=MetricKind.RESTING_HEART_RATE,
                 event_time=BASE, value=90, unit="bpm", seq=1, source="goqii_band")
        e.submit(member_id="m1", device_id="m1_band", metric=MetricKind.STEPS,
                 event_time=BASE + 100, value=2000, unit="count", seq=2, source="goqii_band")
        score = e.score_of("m1")
        self.assertIsNotNone(score)
        self.assertGreater(score.overall, 0)
        aging = e.aging_of("m1")
        self.assertIsNotNone(aging)

    def test_invariant_holds_through_the_engine(self):
        e = fresh_engine()
        enrolled(e, "m1")
        e.submit(member_id="m1", device_id="m1_band", metric=MetricKind.STEPS,
                 event_time=BASE + DAY, value=3000, unit="count", seq=1, source="goqii_band")
        before = e.score_of("m1").as_of
        # a late reading from the phone, older event time
        e.submit(member_id="m1", device_id="m1_phone", metric=MetricKind.STEPS,
                 event_time=BASE, value=9000, unit="count", seq=1, source="apple_health")
        after = e.score_of("m1").as_of
        self.assertEqual(before, after)
        self.assertEqual(after, BASE + DAY)

    def test_seed_population_is_deterministic(self):
        e1 = fresh_engine()
        e2 = fresh_engine()
        ids1 = seed(e1)
        ids2 = seed(e2)
        self.assertEqual(ids1, ids2)
        for mid in ids1:
            s1, s2 = e1.score_of(mid), e2.score_of(mid)
            self.assertEqual(s1.overall, s2.overall)
            self.assertEqual(s1.band, s2.band)

    def test_seed_produces_a_spread_of_bands(self):
        e = fresh_engine()
        ids = seed(e)
        bands = {e.score_of(mid).band for mid in ids}
        self.assertGreaterEqual(len(bands), 2)  # not everyone in one band


if __name__ == "__main__":
    unittest.main()
