"""Regression tests for the public prefix API."""

import unittest
from unittest.mock import call, patch

from solution import prefix, prefix_many


class PrefixTests(unittest.TestCase):
    def test_positive_numbers(self) -> None:
        items = [1, 2, 3, 4]
        result = prefix(items)
        self.assertEqual(result, [1, 3, 6, 10])
        self.assertEqual(len(result), len(items))

    def test_empty_input(self) -> None:
        self.assertEqual(prefix([]), [])

    def test_negative_numbers(self) -> None:
        self.assertEqual(prefix([-2, -3]), [-2, -5])

    def test_mixed_numbers_and_zero(self) -> None:
        self.assertEqual(prefix([2, -5, 0, 4]), [2, -3, -3, 1])

    def test_single_item(self) -> None:
        self.assertEqual(prefix([7]), [7])

    def test_input_is_unchanged_and_result_is_independent(self) -> None:
        items = [2, -5, 4]
        original = items.copy()
        result = prefix(items)
        self.assertEqual(items, original)
        self.assertEqual(result, [2, -3, 1])
        self.assertIsNot(result, items)
        result.append(99)
        self.assertEqual(items, original)


class PrefixManyTests(unittest.TestCase):
    def test_batch_results_and_inputs_are_unchanged(self) -> None:
        items = [1, 2, 3]
        cases = [(items,), ([],), ([-2, 0, 5],), (items,)]
        original_cases = cases.copy()
        original_items = [case[0].copy() for case in cases]

        results = prefix_many(cases)

        self.assertEqual(results, [[1, 3, 6], [], [-2, -2, 3], [1, 3, 6]])
        self.assertEqual(cases, original_cases)
        for case, original_case, original in zip(cases, original_cases, original_items):
            self.assertIs(case, original_case)
            self.assertEqual(case[0], original)
        results[0].append(99)
        self.assertEqual(items, [1, 2, 3])
        self.assertEqual(results[3], [1, 3, 6])

    def test_empty_batch_does_not_call_prefix(self) -> None:
        with patch("solution.prefix") as mocked_prefix:
            self.assertEqual(prefix_many([]), [])
        mocked_prefix.assert_not_called()

    def test_batch_unpacks_positional_arguments_in_order(self) -> None:
        cases = [(1, 2), (), (3,)]
        with patch("solution.prefix", side_effect=[10, 20, 30]) as mocked_prefix:
            self.assertEqual(prefix_many(cases), [10, 20, 30])
        self.assertEqual(mocked_prefix.call_args_list, [call(1, 2), call(), call(3)])

    def test_batch_propagates_first_exception_unchanged_and_stops(self) -> None:
        error = ValueError("original failure")
        cases = [([1],), ([2],), ([3],)]
        with patch("solution.prefix", side_effect=[[1], error, [3]]) as mocked_prefix:
            with self.assertRaises(ValueError) as caught:
                prefix_many(cases)
        self.assertIs(caught.exception, error)
        self.assertEqual(mocked_prefix.call_args_list, [call([1]), call([2])])
        self.assertEqual(cases, [([1],), ([2],), ([3],)])


if __name__ == "__main__":
    unittest.main()
