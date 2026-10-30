import unittest

from alive.core.metrics import MetricKind
from tests.helpers import BASE, enrolled, fresh_engine


class TestWorker(unittest.TestCase):
    def setUp(self):
        self.e = fresh_engine()
        enrolled(self.e, "m1")

    def _submit(self, metric, value, event_time, seq, unit="count"):
        return self.e.submit(member_id="m1", device_id="m1_band", metric=metric,
                             event_time=event_time, value=value, unit=unit, seq=seq, source="goqii_band")

    def test_handle_runs_the_full_pipeline(self):
        score = self._submit(MetricKind.STEPS, 2000, BASE, 1)
        self.assertIsNotNone(score)
        self.assertEqual(score.member_id, "m1")
        # low steps -> a recommendation was derived and delivered
        self.assertGreaterEqual(len(self.e.deliveries), 1)
        self.assertEqual(len(self.e.outbox), 0)  # outbox drained by deliver()

    def test_deliver_drains_outbox(self):
        self._submit(MetricKind.SPO2, 85, BASE, 1, unit="%")
        self.assertEqual(len(self.e.outbox), 0)

    def test_sweep_rescore_all_members(self):
        enrolled(self.e, "m2")
        self._submit(MetricKind.STEPS, 2000, BASE, 1)
        self.e.submit(member_id="m2", device_id="m2_band", metric=MetricKind.STEPS,
                      event_time=BASE, value=3000, unit="count", seq=1, source="goqii_band")
        n = self.e.sweep()
        self.assertEqual(n, 2)
        self.assertIsNotNone(self.e.scheduler.last_sweep)

    def test_score_served_after_handle(self):
        self._submit(MetricKind.STEPS, 2000, BASE, 1)
        self.assertIsNotNone(self.e.score_of("m1"))
        self.assertIsNotNone(self.e.aging_of("m1"))


if __name__ == "__main__":
    unittest.main()
