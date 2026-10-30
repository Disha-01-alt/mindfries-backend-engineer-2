import random
import unittest

from alive.core.metrics import MetricKind
from alive.core.score import RiskBand, band_for, compute
from alive.core.windows import DAY
from tests.helpers import BASE, make_sample


class TestBand(unittest.TestCase):
    def test_band_thresholds(self):
        self.assertEqual(band_for(0), RiskBand.LOW)
        self.assertEqual(band_for(24.99), RiskBand.LOW)
        self.assertEqual(band_for(25), RiskBand.MODERATE)
        self.assertEqual(band_for(49.99), RiskBand.MODERATE)
        self.assertEqual(band_for(50), RiskBand.HIGH)
        self.assertEqual(band_for(74.99), RiskBand.HIGH)
        self.assertEqual(band_for(75), RiskBand.CRITICAL)
        self.assertEqual(band_for(100), RiskBand.CRITICAL)


class TestScore(unittest.TestCase):
    def _healthy(self):
        # Every metric sitting mid-range -> zero risk.
        return [
            make_sample(MetricKind.RESTING_HEART_RATE, BASE, 55, 1),  # <= low -> 0
            make_sample(MetricKind.HRV, BASE, 95, 2),                 # >= high -> 0
            make_sample(MetricKind.STEPS, BASE, 12000, 3),            # >= high -> 0
            make_sample(MetricKind.SPO2, BASE, 99, 4),                # >= high -> 0
            make_sample(MetricKind.BLOOD_GLUCOSE, BASE, 90, 5),       # in range -> 0
        ]

    def test_healthy_member_is_zero_risk(self):
        s = compute("m1", self._healthy(), as_of=BASE)
        self.assertEqual(s.overall, 0.0)
        self.assertEqual(s.band, RiskBand.LOW)
        self.assertEqual(s.sample_count, 5)
        self.assertEqual(s.as_of, BASE)

    def test_elevated_rhr_lower_is_better(self):
        high = compute("m1", [make_sample(MetricKind.RESTING_HEART_RATE, BASE, 95, 1)], as_of=BASE)
        low = compute("m1", [make_sample(MetricKind.RESTING_HEART_RATE, BASE, 55, 1)], as_of=BASE)
        self.assertGreater(high.overall, 0)
        self.assertEqual(low.overall, 0)

    def test_low_steps_higher_is_better(self):
        low = compute("m1", [make_sample(MetricKind.STEPS, BASE, 2000, 1)], as_of=BASE)
        high = compute("m1", [make_sample(MetricKind.STEPS, BASE, 12000, 1)], as_of=BASE)
        self.assertGreater(low.overall, 0)
        self.assertEqual(high.overall, 0)

    def test_glucose_in_range_either_side(self):
        inr = compute("m1", [make_sample(MetricKind.BLOOD_GLUCOSE, BASE, 90, 1)], as_of=BASE)
        hi = compute("m1", [make_sample(MetricKind.BLOOD_GLUCOSE, BASE, 180, 1)], as_of=BASE)
        lo = compute("m1", [make_sample(MetricKind.BLOOD_GLUCOSE, BASE, 50, 1)], as_of=BASE)
        self.assertEqual(inr.overall, 0)
        self.assertGreater(hi.overall, 0)
        self.assertGreater(lo.overall, 0)

    def test_order_independence(self):
        xs = self._healthy() + [
            make_sample(MetricKind.STEPS, BASE + 10, 3000, 6),
            make_sample(MetricKind.SPO2, BASE + 20, 90, 7),
        ]
        a = compute("m1", xs, as_of=BASE + 100)
        shuffled = xs[:]
        random.Random(13).shuffle(shuffled)
        b = compute("m1", shuffled, as_of=BASE + 100)
        self.assertEqual(a, b)

    def test_horizon_excludes_stale_samples(self):
        xs = [
            make_sample(MetricKind.STEPS, BASE - 10 * DAY, 1000, 1),  # outside 7-day horizon
            make_sample(MetricKind.STEPS, BASE, 12000, 2),           # inside
        ]
        s = compute("m1", xs, as_of=BASE)
        self.assertEqual(s.sample_count, 1)
        self.assertEqual(s.overall, 0)  # only the healthy in-horizon step count counts

    def test_sum_metric_is_mean_of_daily_totals(self):
        xs = [
            make_sample(MetricKind.STEPS, BASE, 4000, 1),           # day 0: 4000+2000 = 6000
            make_sample(MetricKind.STEPS, BASE + 100, 2000, 2),
            make_sample(MetricKind.STEPS, BASE + DAY, 12000, 3),    # day 1: 12000
        ]
        s = compute("m1", xs, as_of=BASE + DAY)
        steps = [c for c in s.contributions if c.metric == MetricKind.STEPS][0]
        self.assertAlmostEqual(steps.aggregate, 9000.0, places=3)  # mean(6000, 12000)

    def test_lineage_is_present_and_explained(self):
        s = compute("m1", [make_sample(MetricKind.STEPS, BASE, 2000, 1)], as_of=BASE)
        self.assertEqual(len(s.contributions), 1)
        c = s.contributions[0]
        self.assertEqual(c.metric, MetricKind.STEPS)
        self.assertEqual(c.sample_count, 1)
        self.assertIn("steps", c.note)

    def test_no_data_is_zero_count(self):
        s = compute("m1", [], as_of=BASE)
        self.assertFalse(s.has_data)
        self.assertEqual(s.overall, 0.0)
        self.assertEqual(s.contributions, ())


if __name__ == "__main__":
    unittest.main()
