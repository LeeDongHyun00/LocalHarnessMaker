"""Tests for the public clamp API."""

import unittest

from solution import clamp


class ClampTests(unittest.TestCase):
    def test_values_inside_range_are_unchanged(self) -> None:
        for value, low, high in [(5, 0, 10), (-5, -10, -1), (0, -5, 5)]:
            with self.subTest(value=value, low=low, high=high):
                self.assertEqual(clamp(value, low, high), value)

    def test_values_outside_range_are_clamped(self) -> None:
        cases = [
            (-1, 0, 10, 0),
            (11, 0, 10, 10),
            (-20, -10, -1, -10),
            (0, -10, -1, -1),
        ]
        for value, low, high, expected in cases:
            with self.subTest(value=value, low=low, high=high):
                self.assertEqual(clamp(value, low, high), expected)

    def test_boundaries_are_inclusive(self) -> None:
        for value in (-5, 5):
            with self.subTest(value=value):
                self.assertEqual(clamp(value, -5, 5), value)

    def test_equal_bounds_are_valid(self) -> None:
        for bound in (-3, 0, 3):
            for value in (bound - 1, bound, bound + 1):
                with self.subTest(value=value, bound=bound):
                    self.assertEqual(clamp(value, bound, bound), bound)

    def test_reversed_bounds_raise_value_error(self) -> None:
        for value, low, high in [(0, 10, 5), (7, 10, 5), (15, 10, 5), (-5, -1, -10)]:
            with self.subTest(value=value, low=low, high=high):
                with self.assertRaises(ValueError):
                    clamp(value, low, high)


if __name__ == "__main__":
    unittest.main()
