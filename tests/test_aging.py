import unittest

from alive.core.aging import assess
from alive.core.metrics import MetricKind
from alive.core.score import compute
from tests.helpers import BASE, make_sample


class TestAging(unittest.TestCase):
    def test_fit_member_is_biologically_younger(self):
        samples = [
            make_sample(MetricKind.HRV, BASE, 110, 1),               # high HRV -> younger
            make_sample(MetricKind.RESTING_HEART_RATE, BASE, 50, 2),  # low RHR -> younger
            make_sample(MetricKind.STEPS, BASE, 13000, 3),            # active -> younger
        ]
        score = compute("m1", samples, as_of=BASE)
        a = assess(40, score)
        self.assertTrue(a.is_younger)
        self.assertLess(a.biological_age, 40)
        self.assertEqual(a.chronological_age, 40)

    def test_high_risk_member_is_biologically_older(self):
        samples = [
            make_sample(MetricKind.HRV, BASE, 30, 1),
            make_sample(MetricKind.RESTING_HEART_RATE, BASE, 90, 2),
            make_sample(MetricKind.STEPS, BASE, 2000, 3),
            make_sample(MetricKind.SPO2, BASE, 90, 4),
        ]
        score = compute("m1", samples, as_of=BASE)
        a = assess(50, score)
        self.assertFalse(a.is_younger)
        self.assertGreater(a.biological_age, 50)

    def test_delta_is_capped(self):
        samples = [make_sample(MetricKind.RESTING_HEART_RATE, BASE, 200, 1)]
        score = compute("m1", samples, as_of=BASE)
        a = assess(40, score)
        self.assertLessEqual(a.delta_years, 15.0)
        self.assertGreaterEqual(a.delta_years, -15.0)

    def test_consistency_of_delta(self):
        score = compute("m1", [make_sample(MetricKind.STEPS, BASE, 5000, 1)], as_of=BASE)
        a = assess(45, score)
        self.assertAlmostEqual(a.biological_age, 45 + a.delta_years, places=1)


if __name__ == "__main__":
    unittest.main()
