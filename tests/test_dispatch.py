"""Dispatch tests that hold for BOTH the baseline and the idempotent solution.

These assert what is always true — a fresh alert is delivered, distinct alerts
are each delivered, the dedup key is correct — but deliberately do NOT assert
anything about duplicate suppression, which is exactly what the extension task
changes. The hidden acceptance tests cover at-most-once.
"""

import unittest

from alive.core.events import Alert, Recipient, Recommendation, Severity
from alive.services.dispatch import Dispatcher, _dedup_key
from alive.store.dispatch_log import DispatchLog
from tests.helpers import BASE


def alert(rule="overall_high", recipient="coach_ravi", member="m1", window=BASE):
    return Alert(member_id=member, recipient_id=recipient, recipient_kind=Recipient.COACH,
                 rule=rule, severity=Severity.WARNING, window=window, message="x", event_time=BASE)


class TestDispatch(unittest.TestCase):
    def setUp(self):
        self.dispatcher = Dispatcher(DispatchLog())

    def test_fresh_alert_is_delivered(self):
        self.assertTrue(self.dispatcher.dispatch(alert()))
        self.assertEqual(len(self.dispatcher.deliveries), 1)

    def test_distinct_alerts_are_each_delivered(self):
        self.dispatcher.dispatch(alert(rule="overall_high"))
        self.dispatcher.dispatch(alert(rule="spo2_breach"))
        self.assertEqual(len(self.dispatcher.deliveries), 2)

    def test_alert_dedup_key_is_recipient_and_stable_id(self):
        a = alert()
        self.assertEqual(_dedup_key(a), (a.recipient_id, a.alert_id))

    def test_alert_id_identity_is_member_rule_window(self):
        a1 = alert(window=BASE)
        a2 = alert(window=BASE)            # same member/rule/window
        a3 = alert(window=BASE + 86400)    # different window
        self.assertEqual(a1.alert_id, a2.alert_id)
        self.assertNotEqual(a1.alert_id, a3.alert_id)

    def test_recommendation_dedup_key(self):
        r = Recommendation(member_id="m1", kind="move_more", message="x", window=BASE, event_time=BASE)
        self.assertEqual(_dedup_key(r), ("m1", r.rec_id))


if __name__ == "__main__":
    unittest.main()
