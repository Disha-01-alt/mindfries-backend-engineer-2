import unittest

from alive.core.errors import UnitMismatchError
from alive.core.metrics import MetricKind
from alive.core.units import normalize


class TestUnits(unittest.TestCase):
    def test_identity_canonical_units(self):
        self.assertEqual(normalize(MetricKind.RESTING_HEART_RATE, 60, "bpm"), 60)
        self.assertEqual(normalize(MetricKind.STEPS, 8000, "count"), 8000)
        self.assertEqual(normalize(MetricKind.SPO2, 97, "%"), 97)

    def test_glucose_mmol_to_mgdl(self):
        self.assertAlmostEqual(normalize(MetricKind.BLOOD_GLUCOSE, 6.0, "mmol/L"), 108.1092, places=3)

    def test_weight_lb_to_kg(self):
        self.assertAlmostEqual(normalize(MetricKind.BODY_WEIGHT, 150, "lb"), 68.0388555, places=4)

    def test_temp_f_to_c(self):
        self.assertAlmostEqual(normalize(MetricKind.BODY_TEMP, 98.6, "degF"), 37.0, places=4)
        self.assertAlmostEqual(normalize(MetricKind.BODY_TEMP, 32, "degF"), 0.0, places=6)

    def test_sleep_hours_to_minutes(self):
        self.assertAlmostEqual(normalize(MetricKind.SLEEP, 8, "h"), 480.0, places=6)

    def test_hrv_seconds_to_ms(self):
        self.assertAlmostEqual(normalize(MetricKind.HRV, 0.05, "s"), 50.0, places=6)

    def test_energy_kj_to_kcal(self):
        self.assertAlmostEqual(normalize(MetricKind.ACTIVE_ENERGY, 418.4, "kJ"), 100.0, places=4)

    def test_unit_aliases_are_accepted(self):
        self.assertEqual(normalize(MetricKind.RESTING_HEART_RATE, 60, "beats/min"), 60)
        self.assertAlmostEqual(normalize(MetricKind.BODY_TEMP, 98.6, "Fahrenheit"), 37.0, places=4)

    def test_unconvertible_unit_is_rejected(self):
        with self.assertRaises(UnitMismatchError):
            normalize(MetricKind.BLOOD_GLUCOSE, 6.0, "mmHg")
        with self.assertRaises(UnitMismatchError):
            normalize(MetricKind.STEPS, 8000, "km")


if __name__ == "__main__":
    unittest.main()
