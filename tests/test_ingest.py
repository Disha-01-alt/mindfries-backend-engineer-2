import unittest

from alive.core.errors import EnrollmentError, SequenceError, UnitMismatchError
from alive.core.metrics import MetricKind
from tests.helpers import BASE, enrolled, fresh_engine


class TestIngest(unittest.TestCase):
    def setUp(self):
        self.e = fresh_engine()
        self.m = enrolled(self.e)

    def _ingest(self, **kw):
        defaults = dict(member_id=self.m, device_id="m1_band", metric=MetricKind.STEPS,
                        event_time=BASE, value=5000, unit="count", seq=1, source="goqii_band")
        defaults.update(kw)
        return self.e.ingest.ingest(**defaults)

    def test_ingest_stores_canonical_value(self):
        s = self._ingest(metric=MetricKind.BLOOD_GLUCOSE, value=6.0, unit="mmol/L")
        self.assertAlmostEqual(s.value, 108.1092, places=3)
        self.assertEqual(s.unit, "mg/dL")

    def test_ingest_stamps_processing_time_from_clock(self):
        s = self._ingest()
        self.assertEqual(s.ingested_at, BASE)  # ManualClock is at BASE

    def test_unknown_member_rejected(self):
        with self.assertRaises(EnrollmentError):
            self._ingest(member_id="ghost")

    def test_unregistered_device_rejected(self):
        with self.assertRaises(EnrollmentError):
            self._ingest(device_id="no_such_device")

    def test_device_belonging_to_another_member_rejected(self):
        enrolled(self.e, "m2")
        with self.assertRaises(EnrollmentError):
            self._ingest(member_id=self.m, device_id="m2_band")

    def test_bad_unit_rejected(self):
        with self.assertRaises(UnitMismatchError):
            self._ingest(metric=MetricKind.BLOOD_GLUCOSE, value=6, unit="mmHg")

    def test_sequence_guard_applies_through_ingest(self):
        self._ingest(event_time=BASE + 10, seq=2)
        with self.assertRaises(SequenceError):
            self._ingest(event_time=BASE, seq=1)


if __name__ == "__main__":
    unittest.main()
