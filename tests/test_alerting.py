import unittest

from alive.core.events import Alert, Recipient
from alive.core.metrics import MetricKind
from alive.core.score import compute
from tests.helpers import BASE, enrolled, fresh_engine, make_sample


class TestAlerting(unittest.TestCase):
    def setUp(self):
        self.e = fresh_engine()
        enrolled(self.e, "m1", coach="coach_ravi")

    def _high_risk_score(self):
        samples = [
            make_sample(MetricKind.SPO2, BASE, 88, 1),
            make_sample(MetricKind.RESTING_HEART_RATE, BASE, 95, 2),
            make_sample(MetricKind.STEPS, BASE, 1500, 3),
            make_sample(MetricKind.BLOOD_GLUCOSE, BASE, 200, 4),
        ]
        return compute("m1", samples, as_of=BASE)

    def test_high_risk_enqueues_a_coach_alert(self):
        score = self._high_risk_score()
        items = self.e.alerting.evaluate(score)
        alerts = [i for i in items if isinstance(i, Alert)]
        self.assertTrue(alerts)
        coach_alerts = [a for a in alerts if a.recipient_kind is Recipient.COACH]
        self.assertTrue(coach_alerts)
        self.assertEqual(coach_alerts[0].recipient_id, "coach_ravi")
        self.assertEqual(len(self.e.outbox), len(items))  # all enqueued

    def test_healthy_score_enqueues_nothing(self):
        score = compute("m1", [make_sample(MetricKind.STEPS, BASE, 12000, 1)], as_of=BASE)
        self.assertEqual(self.e.alerting.evaluate(score), [])
        self.assertEqual(len(self.e.outbox), 0)

    def test_alert_id_is_stable_across_reevaluation(self):
        score = self._high_risk_score()
        a1 = [i for i in self.e.alerting.evaluate(score) if isinstance(i, Alert)]
        self.e.outbox.drain()
        a2 = [i for i in self.e.alerting.evaluate(score) if isinstance(i, Alert)]
        self.assertEqual({a.alert_id for a in a1}, {a.alert_id for a in a2})

    def test_critical_metric_breach_escalates(self):
        # A dangerously low SpO2 should produce a critical coach alert on its own.
        score = compute("m1", [make_sample(MetricKind.SPO2, BASE, 85, 1)], as_of=BASE)
        alerts = [i for i in self.e.alerting.evaluate(score) if isinstance(i, Alert)]
        self.assertTrue(any(a.rule.startswith("spo2") or a.severity.value == "critical" for a in alerts))


if __name__ == "__main__":
    unittest.main()
