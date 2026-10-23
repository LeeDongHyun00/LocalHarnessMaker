"""Tests for the public clamp API."""

import unittest

from solution import clamp


class ClampTests(unittest.TestCase):
    def test_ordinary_inputs(self) -> None:
        for value, low, high, expected in (
            (5, 0, 10, 5),
            (-5, 0, 10, 0),
            (15, 0, 10, 10),
            (-5, -10, -1, -5),
            (-20, -10, -1, -10),
            (0, -10, -1, -1),
        ):
            with self.subTest(value=value, low=low, high=high):
                self.assertEqual(clamp(value, low, high), expected)

    def test_inclusive_boundaries(self) -> None:
        self.assertEqual(clamp(0, 0, 10), 0)
        self.assertEqual(clamp(10, 0, 10), 10)

    def test_equal_bounds(self) -> None:
        for value in (-100, 3, 100):
            with self.subTest(value=value):
                self.assertEqual(clamp(value, 3, 3), 3)

    def test_reversed_bounds_raise_value_error(self) -> None:
        for value in (-100, 0, 100):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    clamp(value, 10, -10)


if __name__ == "__main__":
    unittest.main()
