"""Tests for the public clamp API."""

import unittest

from solution import clamp


class ClampTests(unittest.TestCase):
    def test_ordinary_values(self) -> None:
        cases = (
            (5, 0, 10, 5),
            (-3, 0, 10, 0),
            (15, 0, 10, 10),
            (-5, -10, -1, -5),
            (-20, -10, -1, -10),
            (0, -10, -1, -1),
            (0, -10, 10, 0),
            (10**100, -10**101, 10**101, 10**100),
        )
        for value, low, high, expected in cases:
            with self.subTest(value=value, low=low, high=high):
                self.assertEqual(clamp(value, low, high), expected)

    def test_inclusive_boundaries(self) -> None:
        self.assertEqual(clamp(-10, -10, 10), -10)
        self.assertEqual(clamp(10, -10, 10), 10)

    def test_equal_bounds(self) -> None:
        for value in (-100, 5, 100):
            with self.subTest(value=value):
                self.assertEqual(clamp(value, 5, 5), 5)

    def test_reversed_bounds_raise_value_error(self) -> None:
        for value, low, high in ((0, 10, 1), (5, 10, 1), (20, 10, 1), (0, 0, -1)):
            with self.subTest(value=value, low=low, high=high):
                with self.assertRaises(ValueError):
                    clamp(value, low, high)

    def test_non_numeric_inputs_raise_type_error(self) -> None:
        for arguments in (
            (None, 0, 10),
            (5, None, 10),
            (5, 0, None),
            ("invalid", 0, 10),
            (5, "invalid", 10),
            (5, 0, "invalid"),
        ):
            with self.subTest(arguments=arguments):
                with self.assertRaises(TypeError):
                    clamp(*arguments)


if __name__ == "__main__":
    unittest.main()
