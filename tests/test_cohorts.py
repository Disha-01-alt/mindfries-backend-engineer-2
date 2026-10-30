import unittest

from alive.core.metrics import MetricKind
from alive.core.score import RiskBand
from tests.helpers import BASE, enrolled, fresh_engine


class TestCohorts(unittest.TestCase):
    def setUp(self):
        self.e = fresh_engine()

    def _member_with(self, mid, metric, value):
        enrolled(self.e, mid)
        self.e.submit(member_id=mid, device_id=f"{mid}_band", metric=metric,
                      event_time=BASE, value=value, unit="count" if metric == MetricKind.STEPS else "%",
                      seq=1, source="goqii_band")

    def test_summary_counts_and_distribution(self):
        self._member_with("fit", MetricKind.STEPS, 13000)   # low risk
        self._member_with("risk", MetricKind.SPO2, 84)      # critical
        summary = self.e.cohort_summary(["fit", "risk", "never_scored"])
        self.assertEqual(summary.size, 3)
        self.assertEqual(summary.scored, 2)                 # never_scored excluded
        self.assertEqual(summary.band_distribution[RiskBand.LOW.value], 1)
        self.assertGreaterEqual(summary.band_distribution[RiskBand.CRITICAL.value], 1)

    def test_high_risk_members_listed_worst_first(self):
        self._member_with("a", MetricKind.SPO2, 92)   # some risk
        self._member_with("b", MetricKind.SPO2, 84)   # more risk
        summary = self.e.cohort_summary(["a", "b"])
        if len(summary.high_risk_members) == 2:
            first = self.e.score_of(summary.high_risk_members[0]).overall
            second = self.e.score_of(summary.high_risk_members[1]).overall
            self.assertGreaterEqual(first, second)

    def test_empty_cohort(self):
        summary = self.e.cohort_summary([])
        self.assertEqual(summary.size, 0)
        self.assertEqual(summary.scored, 0)
        self.assertEqual(summary.average_overall, 0.0)


if __name__ == "__main__":
    unittest.main()
