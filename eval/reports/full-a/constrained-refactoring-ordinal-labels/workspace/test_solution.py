"""Tests for both public ordinal formatters."""

import unittest

from solution import ordinal, ordinal_legacy


class OrdinalTests(unittest.TestCase):
    def test_ordinal_suffixes(self) -> None:
        cases = {
            0: '0th', 1: '1st', 2: '2nd', 3: '3rd', 4: '4th',
            10: '10th', 11: '11th', 12: '12th', 13: '13th',
            20: '20th', 21: '21st', 22: '22nd', 23: '23rd',
            100: '100th', 111: '111th', 112: '112th', 113: '113th',
            121: '121st', 122: '122nd', 123: '123rd',
            10**100 + 1: str(10**100 + 1) + 'st',
        }
        for formatter in (ordinal, ordinal_legacy):
            for value, expected in cases.items():
                with self.subTest(formatter=formatter.__name__, value=value):
                    result = formatter(value=value)
                    self.assertIsInstance(result, str)
                    self.assertEqual(result, expected)

    def test_negative_values_raise(self) -> None:
        for formatter in (ordinal, ordinal_legacy):
            for value in (-1, -11, -100):
                with self.subTest(formatter=formatter.__name__, value=value):
                    with self.assertRaisesRegex(
                        ValueError, '^nonnegative value required$'
                    ):
                        formatter(value)

    def test_source_collection_is_unchanged(self) -> None:
        values = [0, 1, 2, 3, 11, 12, 13, 111]
        original = values.copy()
        for formatter in (ordinal, ordinal_legacy):
            results = list(map(formatter, values))
            self.assertEqual(values, original)
            self.assertEqual(
                results, ['0th', '1st', '2nd', '3rd', '11th', '12th', '13th', '111th']
            )


if __name__ == '__main__':
    unittest.main()
