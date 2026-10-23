"""Tests for the public prefix API."""

import unittest

from solution import prefix


class PrefixTests(unittest.TestCase):
    def test_ordinary_inputs(self) -> None:
        self.assertEqual(prefix([1, 2, 3, 4]), [1, 3, 6, 10])
        self.assertEqual(prefix([5, 0, 2, 0]), [5, 5, 7, 7])

    def test_negative_numbers(self) -> None:
        self.assertEqual(prefix([3, -5, 2, -4]), [3, -2, 0, -4])
        self.assertEqual(prefix([-1, -2, -3]), [-1, -3, -6])

    def test_empty_input(self) -> None:
        self.assertEqual(prefix([]), [])

    def test_single_element(self) -> None:
        for value in (0, 7, -7):
            with self.subTest(value=value):
                self.assertEqual(prefix([value]), [value])

    def test_input_is_not_mutated(self) -> None:
        items = [2, -1, 4]
        original = items.copy()

        result = prefix(items)

        self.assertEqual(result, [2, 1, 5])
        self.assertEqual(items, original)
        self.assertIsNot(result, items)


if __name__ == "__main__":
    unittest.main()
