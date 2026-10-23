"""Tests for the public partition API."""

import unittest

from solution import partition


class PartitionTests(unittest.TestCase):
    def test_mixed_values_preserve_order_duplicates_and_input(self) -> None:
        items = [3, -2, 0, -1, 3, 0, -2, 1]
        original = items.copy()

        result = partition(items)

        self.assertEqual(result, ([-2, -1, -2], [0, 0], [3, 3, 1]))
        self.assertIsInstance(result, tuple)
        for group in result:
            self.assertIsInstance(group, list)
            self.assertIsNot(group, items)
        self.assertEqual(items, original)

    def test_empty_input_returns_independent_empty_lists(self) -> None:
        items: list[int] = []
        negatives, zeros, positives = partition(items)

        self.assertEqual((negatives, zeros, positives), ([], [], []))
        negatives.append(-1)
        self.assertEqual(zeros, [])
        self.assertEqual(positives, [])
        self.assertEqual(items, [])

    def test_boundary_and_single_partition_inputs(self) -> None:
        cases = [
            ([-1], ([-1], [], [])),
            ([0], ([], [0], [])),
            ([1], ([], [], [1])),
            ([0, 0], ([], [0, 0], [])),
            ([-3, -1, -3], ([-3, -1, -3], [], [])),
            ([2, 1, 2], ([], [], [2, 1, 2])),
            ([-10**100, -1, 0, 1, 10**100],
             ([-10**100, -1], [0], [1, 10**100])),
        ]
        for items, expected in cases:
            with self.subTest(items=items):
                original = items.copy()
                self.assertEqual(partition(items), expected)
                self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
