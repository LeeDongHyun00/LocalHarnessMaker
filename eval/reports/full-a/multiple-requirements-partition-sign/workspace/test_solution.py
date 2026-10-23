"""Regression tests for the public partition API."""

import unittest

from solution import partition


class PartitionTests(unittest.TestCase):
    def test_mixed_values_preserve_order_and_duplicates(self) -> None:
        items = [3, -1, 0, -5, 2, 0, -1, 3, -2, 1]

        self.assertEqual(
            partition(items),
            ([-1, -5, -1, -2], [0, 0], [3, 2, 3, 1]),
        )

    def test_empty_input_returns_three_distinct_lists(self) -> None:
        result = partition([])

        self.assertIsInstance(result, tuple)
        self.assertEqual(result, ([], [], []))
        for values in result:
            self.assertIsInstance(values, list)
        self.assertIsNot(result[0], result[1])
        self.assertIsNot(result[1], result[2])
        self.assertIsNot(result[0], result[2])

    def test_single_partition_inputs(self) -> None:
        for items, expected in (
            ([-2, -7, -2], ([-2, -7, -2], [], [])),
            ([0, 0, 0], ([], [0, 0, 0], [])),
            ([4, 1, 4], ([], [], [4, 1, 4])),
        ):
            with self.subTest(items=items):
                self.assertEqual(partition(items), expected)

    def test_input_is_unchanged_and_results_are_independent(self) -> None:
        items = [2, 0, -3, 2, -1, 0]
        original = items.copy()

        result = partition(items)

        self.assertEqual(items, original)
        for values in result:
            self.assertIsNot(values, items)
            values.append(99)
        self.assertEqual(items, original)
        self.assertEqual(partition(items), ([-3, -1], [0, 0], [2, 2]))


if __name__ == "__main__":
    unittest.main()
