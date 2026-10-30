import unittest

from alive.core.dedup import dedupe, prefer, source_priority
from alive.core.metrics import MetricKind
from tests.helpers import BASE, make_sample


class TestDedup(unittest.TestCase):
    def test_same_reading_two_sources_collapses_to_one(self):
        a = make_sample(MetricKind.SPO2, BASE, 97, 1, device_id="phone", source="apple_health")
        b = make_sample(MetricKind.SPO2, BASE, 96, 1, device_id="band", source="goqii_band")
        out = dedupe([a, b])
        self.assertEqual(len(out), 1)

    def test_higher_priority_source_wins(self):
        phone = make_sample(MetricKind.SPO2, BASE, 97, 1, device_id="phone", source="apple_health")
        lab = make_sample(MetricKind.SPO2, BASE, 96, 1, device_id="lab", source="lab")
        self.assertEqual(prefer(phone, lab).source, "lab")
        self.assertEqual(prefer(lab, phone).source, "lab")  # order-independent
        self.assertEqual(dedupe([phone, lab])[0].source, "lab")

    def test_priority_order(self):
        self.assertLess(source_priority("lab"), source_priority("goqii_band"))
        self.assertLess(source_priority("goqii_band"), source_priority("apple_health"))
        self.assertLess(source_priority("apple_health"), source_priority("checkin"))
        self.assertEqual(source_priority("something_unknown"), source_priority("also_unknown"))

    def test_distinct_instants_are_kept_separate(self):
        a = make_sample(MetricKind.HEART_RATE, BASE, 70, 1)
        b = make_sample(MetricKind.HEART_RATE, BASE + 1, 72, 2)
        self.assertEqual(len(dedupe([a, b])), 2)

    def test_dedupe_result_is_order_independent(self):
        xs = [
            make_sample(MetricKind.STEPS, BASE + 2, 100, 3),
            make_sample(MetricKind.STEPS, BASE, 100, 1),
            make_sample(MetricKind.STEPS, BASE + 1, 100, 2),
        ]
        a = dedupe(xs)
        b = dedupe(list(reversed(xs)))
        self.assertEqual(a, b)
        self.assertEqual([s.event_time for s in a], [BASE, BASE + 1, BASE + 2])  # sorted


if __name__ == "__main__":
    unittest.main()
