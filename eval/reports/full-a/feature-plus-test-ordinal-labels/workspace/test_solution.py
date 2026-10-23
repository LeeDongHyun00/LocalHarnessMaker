"""Tests for the public ordinal API."""

import unittest

from solution import ordinal


class OrdinalTests(unittest.TestCase):
    def test_ordinary_values(self) -> None:
        cases = {
            1: "1st", 2: "2nd", 3: "3rd", 4: "4th", 5: "5th",
            6: "6th", 7: "7th", 8: "8th", 9: "9th",
            21: "21st", 22: "22nd", 23: "23rd", 24: "24th",
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(ordinal(value), expected)

    def test_zero_and_suffix_boundaries(self) -> None:
        cases = {
            0: "0th", 10: "10th", 11: "11th", 12: "12th",
            13: "13th", 14: "14th", 20: "20th", 100: "100th",
            101: "101st", 102: "102nd", 103: "103rd", 110: "110th",
            111: "111th", 112: "112th", 113: "113th", 114: "114th",
            121: "121st", 122: "122nd", 123: "123rd",
            10**100 + 11: f"{10**100 + 11}th",
            10**100 + 21: f"{10**100 + 21}st",
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(ordinal(value), expected)

    def test_negative_values_raise_value_error(self) -> None:
        for value in (-1, -2, -11, -100, -(10**100)):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    ordinal(value)


if __name__ == "__main__":
    unittest.main()
