import unittest

from alive.core.errors import SequenceError
from alive.core.metrics import MetricKind
from alive.store.sample_store import SampleStore
from tests.helpers import BASE, make_sample


class TestSampleStore(unittest.TestCase):
    def setUp(self):
        self.store = SampleStore()

    def test_append_and_retrieve(self):
        s = make_sample(MetricKind.STEPS, BASE, 5000, 1)
        self.store.append(s)
        self.assertEqual(self.store.for_member("m1"), [s])
        self.assertEqual(self.store.count(), 1)

    def test_sequence_must_not_go_backwards(self):
        self.store.append(make_sample(MetricKind.STEPS, BASE + 10, 5000, 2))
        with self.assertRaises(SequenceError):
            self.store.append(make_sample(MetricKind.STEPS, BASE, 6000, 1))  # seq 1 < 2

    def test_exact_resend_is_idempotent(self):
        s = make_sample(MetricKind.STEPS, BASE, 5000, 1)
        self.store.append(s)
        again = self.store.append(s)  # identical frame, same seq
        self.assertIs(again, s)
        self.assertEqual(self.store.count(), 1)

    def test_same_seq_different_content_conflicts(self):
        self.store.append(make_sample(MetricKind.STEPS, BASE, 5000, 1))
        with self.assertRaises(SequenceError):
            self.store.append(make_sample(MetricKind.STEPS, BASE + 1, 6000, 1))  # seq reused

    def test_sequence_is_per_device_and_metric(self):
        # Same seq number is fine across different metrics / devices.
        self.store.append(make_sample(MetricKind.STEPS, BASE, 5000, 1))
        self.store.append(make_sample(MetricKind.HRV, BASE, 50, 1))  # different metric
        self.store.append(make_sample(MetricKind.STEPS, BASE, 70, 1, device_id="m1_phone"))  # different device
        self.assertEqual(self.store.count(), 3)

    def test_event_time_may_arrive_out_of_order(self):
        # Monotonic SEQ, out-of-order EVENT TIME — the normal late-arrival case.
        self.store.append(make_sample(MetricKind.HEART_RATE, BASE + 100, 70, 1))
        self.store.append(make_sample(MetricKind.HEART_RATE, BASE, 72, 2))  # older event, newer seq
        self.assertEqual(self.store.count(), 2)

    def test_max_event_time_is_the_watermark(self):
        self.store.append(make_sample(MetricKind.HEART_RATE, BASE + 100, 70, 1))
        self.store.append(make_sample(MetricKind.HEART_RATE, BASE, 72, 2))  # late, older
        self.assertEqual(self.store.max_event_time("m1"), BASE + 100)  # not the last appended
        self.assertIsNone(self.store.max_event_time("nobody"))


if __name__ == "__main__":
    unittest.main()
