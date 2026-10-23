"""Tests for the public ordinal formatter."""

import unittest

from solution import ordinal


class OrdinalTests(unittest.TestCase):
    def test_ordinary_ordinals(self) -> None:
        cases = {
            1: "1st",
            2: "2nd",
            3: "3rd",
            4: "4th",
            9: "9th",
            21: "21st",
            22: "22nd",
            23: "23rd",
            24: "24th",
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(ordinal(value), expected)

    def test_teen_suffix_exceptions(self) -> None:
        cases = {
            11: "11th",
            12: "12th",
            13: "13th",
            111: "111th",
            112: "112th",
            113: "113th",
            211: "211th",
            212: "212th",
            213: "213th",
            1011: "1011th",
            1012: "1012th",
            1013: "1013th",
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(ordinal(value), expected)

    def test_zero_and_digit_boundaries(self) -> None:
        cases = {
            0: "0th",
            10: "10th",
            14: "14th",
            20: "20th",
            99: "99th",
            100: "100th",
            101: "101st",
            102: "102nd",
            103: "103rd",
            110: "110th",
            114: "114th",
            120: "120th",
            121: "121st",
            999: "999th",
            1000: "1000th",
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(ordinal(value), expected)

    def test_large_integer(self) -> None:
        self.assertEqual(
            ordinal(10**30 + 1),
            "1000000000000000000000000000001st",
        )

    def test_negative_integers_raise_value_error(self) -> None:
        for value in (-1, -2, -3, -11, -100, -(10**30)):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    ordinal(value)


if __name__ == "__main__":
    unittest.main()
