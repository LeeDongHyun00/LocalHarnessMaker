"""Tests for the public pairs API."""

import unittest

from solution import pairs


class PairsTests(unittest.TestCase):
    def test_ordinary_inputs_preserve_order_and_overlap(self) -> None:
        self.assertEqual(pairs([1, 2, 3]), [(1, 2), (2, 3)])
        self.assertEqual(
            pairs([4, -1, -1, 0]), [(4, -1), (-1, -1), (-1, 0)]
        )

    def test_two_items_produce_one_pair(self) -> None:
        self.assertEqual(pairs([7, 8]), [(7, 8)])

    def test_fewer_than_two_items_produce_no_pairs(self) -> None:
        self.assertEqual(pairs([]), [])
        self.assertEqual(pairs([5]), [])

    def test_input_is_not_mutated(self) -> None:
        items = [3, 1, 2]
        original = items.copy()
        self.assertEqual(pairs(items), [(3, 1), (1, 2)])
        self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
