import unittest

from alive.core.metrics import MetricKind
from alive.core.score import compute
from alive.services import recommendations
from tests.helpers import BASE, make_sample


class TestRecommendations(unittest.TestCase):
    def test_low_steps_recommends_moving(self):
        score = compute("m1", [make_sample(MetricKind.STEPS, BASE, 2000, 1)], as_of=BASE)
        recs = recommendations.build(score)
        kinds = {r.kind for r in recs}
        self.assertIn("move_more", kinds)

    def test_healthy_metric_recommends_nothing(self):
        score = compute("m1", [make_sample(MetricKind.STEPS, BASE, 12000, 1)], as_of=BASE)
        self.assertEqual(recommendations.build(score), [])

    def test_glucose_out_of_range_recommends_checkin(self):
        score = compute("m1", [make_sample(MetricKind.BLOOD_GLUCOSE, BASE, 190, 1)], as_of=BASE)
        kinds = {r.kind for r in recommendations.build(score)}
        self.assertIn("glucose_checkin", kinds)

    def test_recommendation_has_stable_id(self):
        score = compute("m1", [make_sample(MetricKind.STEPS, BASE, 2000, 1)], as_of=BASE)
        r1 = recommendations.build(score)[0]
        r2 = recommendations.build(score)[0]
        self.assertEqual(r1.rec_id, r2.rec_id)  # same score -> same id


if __name__ == "__main__":
    unittest.main()
