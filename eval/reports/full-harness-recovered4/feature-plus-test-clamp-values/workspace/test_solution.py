"""Tests for the public clamp function."""

import unittest

from solution import clamp


class ClampTests(unittest.TestCase):
    def test_ordinary_values(self) -> None:
        for value, low, high, expected in (
            (5, 0, 10, 5),
            (-5, 0, 10, 0),
            (15, 0, 10, 10),
            (-5, -10, -1, -5),
        ):
            with self.subTest(value=value, low=low, high=high):
                self.assertEqual(clamp(value, low, high), expected)

    def test_inclusive_and_equal_bounds(self) -> None:
        self.assertEqual(clamp(0, 0, 10), 0)
        self.assertEqual(clamp(10, 0, 10), 10)
        for value in (-10, 3, 20):
            with self.subTest(value=value):
                self.assertEqual(clamp(value, 3, 3), 3)

    def test_reversed_bounds(self) -> None:
        for value in (-5, 5, 15):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    clamp(value, 10, 0)

    def test_invalid_numeric_inputs(self) -> None:
        for args in ((None, 0, 10), (5, None, 10), (5, 0, None)):
            with self.subTest(args=args):
                with self.assertRaises(TypeError):
                    clamp(*args)


if __name__ == "__main__":
    unittest.main()
