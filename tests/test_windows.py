import unittest

from alive.core.windows import DAY, HOUR, Window, window_for, window_start, windows_covering


class TestWindows(unittest.TestCase):
    def test_window_start_floors_to_boundary(self):
        self.assertEqual(window_start(DAY + 100, DAY), DAY)
        self.assertEqual(window_start(DAY - 1, DAY), 0.0)
        self.assertEqual(window_start(2 * DAY, DAY), 2 * DAY)

    def test_half_open_boundary_belongs_to_starting_window(self):
        # An event exactly on a boundary is in the window that STARTS there.
        w = window_for(DAY, DAY)
        self.assertEqual(w.start, DAY)
        self.assertTrue(w.contains(DAY))          # start is inclusive
        self.assertFalse(w.contains(2 * DAY))     # end is exclusive
        self.assertFalse(w.contains(DAY - 0.001))

    def test_window_for_wraps_event(self):
        w = window_for(DAY + 5 * HOUR, DAY)
        self.assertEqual((w.start, w.end), (DAY, 2 * DAY))

    def test_windows_covering_is_contiguous_and_ordered(self):
        ws = windows_covering(DAY + 100, 3 * DAY + 50, DAY)
        self.assertEqual([w.start for w in ws], [DAY, 2 * DAY, 3 * DAY])
        for a, b in zip(ws, ws[1:]):
            self.assertEqual(a.end, b.start)  # no gaps, no overlaps

    def test_empty_range_covers_nothing(self):
        self.assertEqual(windows_covering(DAY, DAY, DAY), [])
        self.assertEqual(windows_covering(DAY + 10, DAY, DAY), [])

    def test_bad_window_rejected(self):
        with self.assertRaises(ValueError):
            Window(10, 10)
        with self.assertRaises(ValueError):
            window_start(100, 0)


if __name__ == "__main__":
    unittest.main()
