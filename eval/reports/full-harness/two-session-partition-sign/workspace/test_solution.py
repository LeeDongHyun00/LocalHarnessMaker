"""Regression tests for the public partition API."""

import unittest
from unittest.mock import call, patch

from solution import partition, partition_many


class PartitionTests(unittest.TestCase):
    def test_mixed_values_preserve_order_and_duplicates(self) -> None:
        self.assertEqual(
            partition([3, -2, 0, -1, 3, 0, -2, 1]),
            ([-2, -1, -2], [0, 0], [3, 3, 1]),
        )

    def test_empty_input(self) -> None:
        self.assertEqual(partition([]), ([], [], []))

    def test_single_partition_inputs(self) -> None:
        for items, expected in [
            ([-3, -1, -3], ([-3, -1, -3], [], [])),
            ([0, 0], ([], [0, 0], [])),
            ([2, 1, 2], ([], [], [2, 1, 2])),
        ]:
            with self.subTest(items=items):
                self.assertEqual(partition(items), expected)

    def test_input_is_unchanged_and_output_lists_are_independent(self) -> None:
        items = [1, 0, -1, 1]
        original = items.copy()
        negatives, zeros, positives = partition(items)
        self.assertEqual(items, original)
        negatives.append(-2)
        self.assertEqual(zeros, [0])
        self.assertEqual(positives, [1, 1])
        zeros.append(0)
        positives.append(2)
        self.assertEqual(items, original)


class PartitionManyTests(unittest.TestCase):
    def test_batch_preserves_order_and_inputs(self) -> None:
        items = [3, -2, 0, -2]
        cases = [(items,), ([],), ([0, 2, -1],), (items,)]
        original = [(case[0].copy(),) for case in cases]
        results = partition_many(cases)
        self.assertEqual(
            results,
            [([-2, -2], [0], [3]), ([], [], []),
             ([-1], [0], [2]), ([-2, -2], [0], [3])],
        )
        self.assertEqual(cases, original)
        self.assertIs(cases[0][0], items)
        results[0][0].append(-3)
        self.assertEqual(results[3][0], [-2, -2])
        self.assertEqual(cases, original)

    def test_empty_batch_does_not_call_partition(self) -> None:
        with patch("solution.partition") as mocked:
            self.assertEqual(partition_many([]), [])
        mocked.assert_not_called()

    def test_calls_partition_once_per_case_with_positional_arguments(self) -> None:
        cases = [(1, 2), (), (3,)]
        with patch("solution.partition", side_effect=["first", "second", "third"]) as mocked:
            self.assertEqual(partition_many(cases), ["first", "second", "third"])
        self.assertEqual(mocked.call_args_list, [call(1, 2), call(), call(3)])

    def test_first_exception_propagates_unchanged_and_stops_batch(self) -> None:
        cases = [([1],), ([2],), ([3],)]
        error = ValueError("partition failed")
        with patch("solution.partition", side_effect=[([], [], [1]), error]) as mocked:
            with self.assertRaises(ValueError) as caught:
                partition_many(cases)
        self.assertIs(caught.exception, error)
        self.assertEqual(mocked.call_args_list, [call([1]), call([2])])
        self.assertEqual(cases, [([1],), ([2],), ([3],)])


if __name__ == "__main__":
    unittest.main()
