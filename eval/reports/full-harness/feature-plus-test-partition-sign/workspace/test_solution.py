"""Tests for the public partition API."""

import unittest

from solution import partition


class PartitionTests(unittest.TestCase):
    def test_mixed_values_preserve_order_duplicates_and_input(self):
        items = [3, -2, 0, -1, 3, 0, -2, 1]
        original = items.copy()

        self.assertEqual(partition(items), ([-2, -1, -2], [0, 0], [3, 3, 1]))
        self.assertEqual(items, original)

    def test_empty_input(self):
        items: list[int] = []
        result = partition(items)

        self.assertEqual(result, ([], [], []))
        self.assertEqual(items, [])
        self.assertIsNot(result[0], result[1])
        self.assertIsNot(result[1], result[2])
        self.assertIsNot(result[0], result[2])

    def test_boundary_and_single_partition_inputs(self):
        cases = [
            ([-1, 0, 1], ([-1], [0], [1])),
            ([-1], ([-1], [], [])),
            ([0], ([], [0], [])),
            ([1], ([], [], [1])),
            ([-3, -1, -3], ([-3, -1, -3], [], [])),
            ([0, 0], ([], [0, 0], [])),
            ([3, 1, 3], ([], [], [3, 1, 3])),
            ([-10**100, 10**100], ([-10**100], [], [10**100])),
        ]
        for items, expected in cases:
            with self.subTest(items=items):
                original = items.copy()
                self.assertEqual(partition(items), expected)
                self.assertEqual(items, original)

    def test_result_lists_do_not_alias_input(self):
        for items in ([-1], [0], [1]):
            with self.subTest(items=items):
                original = items.copy()
                for group in partition(items):
                    group.append(42)
                self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
