"""Regression tests for the public partition API."""

import unittest
from unittest.mock import call, patch

from solution import partition, partition_many


class PartitionTests(unittest.TestCase):
    def test_mixed_values_preserve_order_and_duplicates(self) -> None:
        self.assertEqual(
            partition([3, -2, 0, -5, 3, 0, 1, -2]),
            ([-2, -5, -2], [0, 0], [3, 3, 1]),
        )

    def test_empty_input(self) -> None:
        self.assertEqual(partition([]), ([], [], []))

    def test_single_partition_inputs(self) -> None:
        for items, expected in (
            ([-3, -1, -3], ([-3, -1, -3], [], [])),
            ([0, 0], ([], [0, 0], [])),
            ([4, 2, 4], ([], [], [4, 2, 4])),
        ):
            with self.subTest(items=items):
                self.assertEqual(partition(items), expected)

    def test_input_is_unchanged_and_results_are_independent(self) -> None:
        items = [-1, 0, 2, -1]
        original = items.copy()
        result = partition(items)
        self.assertEqual(items, original)
        for group in result:
            self.assertIsInstance(group, list)
            self.assertIsNot(group, items)
        self.assertIsNot(result[0], result[1])
        self.assertIsNot(result[1], result[2])
        self.assertIsNot(result[0], result[2])
        result[0].append(-9)
        self.assertEqual(items, original)
        self.assertEqual(partition(items), ([-1, -1], [0], [2]))


class PartitionManyTests(unittest.TestCase):
    def test_batch_results_follow_case_order(self) -> None:
        self.assertEqual(
            partition_many([([3, -2, 0, -2],), ([],), ([0, 4, -1],)]),
            [([-2, -2], [0], [3]), ([], [], []), ([-1], [0], [4])],
        )

    def test_empty_batch(self) -> None:
        self.assertEqual(partition_many([]), [])

    def test_cases_and_arguments_are_unchanged(self) -> None:
        items = [-1, 0, 2]
        cases = [(items,), (items,)]
        original_cases = cases.copy()
        original_items = items.copy()
        results = partition_many(cases)
        self.assertEqual(cases, original_cases)
        self.assertEqual(items, original_items)
        for actual, original in zip(cases, original_cases):
            self.assertIs(actual, original)
            self.assertIs(actual[0], items)
        results[0][0].append(-9)
        self.assertEqual(results[1], ([-1], [0], [2]))
        self.assertEqual(items, original_items)

    def test_first_exception_is_propagated_unchanged_and_stops_batch(self) -> None:
        error = ValueError("first failure")
        cases = [([1],), ([-1],), ([0],)]
        with patch("solution.partition", side_effect=[([], [], [1]), error]) as mock:
            with self.assertRaises(ValueError) as caught:
                partition_many(cases)
        self.assertIs(caught.exception, error)
        self.assertEqual(mock.call_args_list, [call([1]), call([-1])])
        self.assertEqual(cases, [([1],), ([-1],), ([0],)])

    def test_invalid_positional_arguments_propagate_type_error(self) -> None:
        for case in ((), ([1], [2])):
            with self.subTest(case=case):
                with self.assertRaises(TypeError):
                    partition_many([case])


if __name__ == "__main__":
    unittest.main()
