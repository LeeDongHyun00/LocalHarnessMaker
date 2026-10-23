"""Tests for the public pairs API."""

import unittest

from solution import pairs


class PairsTests(unittest.TestCase):
    def test_ordinary_inputs(self) -> None:
        cases = [
            ([1, 2, 3], [(1, 2), (2, 3)]),
            ([0, -2, -2, 4], [(0, -2), (-2, -2), (-2, 4)]),
        ]
        for items, expected in cases:
            with self.subTest(items=items):
                self.assertEqual(pairs(items), expected)

    def test_two_items(self) -> None:
        self.assertEqual(pairs([5, 9]), [(5, 9)])

    def test_single_item(self) -> None:
        self.assertEqual(pairs([7]), [])

    def test_empty_input(self) -> None:
        self.assertEqual(pairs([]), [])

    def test_input_is_not_mutated(self) -> None:
        items = [3, 1, 2]
        original = items.copy()

        self.assertEqual(pairs(items), [(3, 1), (1, 2)])
        self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
