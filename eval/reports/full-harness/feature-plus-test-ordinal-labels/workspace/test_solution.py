"""Tests for the public ordinal formatter."""

import unittest

from solution import ordinal


class OrdinalTests(unittest.TestCase):
    def test_ordinary_values(self) -> None:
        for value, expected in {
            1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 9: "9th",
            21: "21st", 22: "22nd", 23: "23rd", 24: "24th",
        }.items():
            with self.subTest(value=value):
                self.assertEqual(ordinal(value), expected)

    def test_zero_and_suffix_boundaries(self) -> None:
        for value, expected in {
            0: "0th", 10: "10th", 11: "11th", 12: "12th",
            13: "13th", 14: "14th", 100: "100th", 101: "101st",
            102: "102nd", 103: "103rd", 110: "110th", 111: "111th",
            112: "112th", 113: "113th", 114: "114th", 121: "121st",
            1011: "1011th", 1012: "1012th", 1013: "1013th",
            10**30 + 1: f"{10**30 + 1}st",
        }.items():
            with self.subTest(value=value):
                self.assertEqual(ordinal(value), expected)

    def test_negative_values_raise_value_error(self) -> None:
        for value in (-1, -2, -11, -113, -(10**30)):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    ordinal(value)


if __name__ == "__main__":
    unittest.main()
