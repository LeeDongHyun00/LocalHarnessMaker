"""Regression tests for the public ordinal API."""

import unittest

from solution import ordinal


class OrdinalTests(unittest.TestCase):
    def test_standard_suffixes(self) -> None:
        cases = (
            (1, "1st"),
            (2, "2nd"),
            (3, "3rd"),
            (4, "4th"),
            (5, "5th"),
            (6, "6th"),
            (7, "7th"),
            (8, "8th"),
            (9, "9th"),
            (10, "10th"),
            (14, "14th"),
            (21, "21st"),
            (22, "22nd"),
            (23, "23rd"),
            (24, "24th"),
            (100, "100th"),
            (101, "101st"),
            (102, "102nd"),
            (103, "103rd"),
            (114, "114th"),
            (121, "121st"),
            (122, "122nd"),
            (123, "123rd"),
        )
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(ordinal(value), expected)

    def test_teen_endings_use_th(self) -> None:
        cases = (
            (11, "11th"),
            (12, "12th"),
            (13, "13th"),
            (111, "111th"),
            (112, "112th"),
            (113, "113th"),
            (1011, "1011th"),
            (1012, "1012th"),
            (1013, "1013th"),
        )
        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(ordinal(value), expected)

    def test_zero(self) -> None:
        self.assertEqual(ordinal(0), "0th")

    def test_negative_values_raise_value_error(self) -> None:
        for value in (-1, -2, -3, -11, -112, -1000):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    ordinal(value)

    def test_preserves_source_values_and_collection_order(self) -> None:
        values = [113, 0, 3, 112, 1, 11, 2, 111, 3]
        original_values = values.copy()

        results = [ordinal(value) for value in values]

        self.assertEqual(
            results,
            ["113th", "0th", "3rd", "112th", "1st", "11th", "2nd", "111th", "3rd"],
        )
        self.assertEqual(values, original_values)


if __name__ == "__main__":
    unittest.main()
