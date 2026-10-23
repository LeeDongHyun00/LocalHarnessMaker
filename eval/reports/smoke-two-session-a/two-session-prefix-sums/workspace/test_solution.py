"""Regression tests for the public prefix API."""

import unittest
from unittest.mock import call, patch

from solution import prefix, prefix_many


class PrefixTests(unittest.TestCase):
    def test_positive_numbers(self) -> None:
        self.assertEqual(prefix([1, 2, 3, 4]), [1, 3, 6, 10])

    def test_empty_input(self) -> None:
        self.assertEqual(prefix([]), [])

    def test_negative_numbers_and_zero(self) -> None:
        self.assertEqual(prefix([-3, 0, 5, -7]), [-3, -3, 2, -5])

    def test_single_element(self) -> None:
        self.assertEqual(prefix([-5]), [-5])

    def test_input_is_unchanged_and_result_is_independent(self) -> None:
        items = [2, -1, 4]
        result = prefix(items)
        self.assertEqual(items, [2, -1, 4])
        self.assertEqual(result, [2, 1, 5])
        self.assertIsNot(result, items)
        result.append(99)
        self.assertEqual(items, [2, -1, 4])


class PrefixManyTests(unittest.TestCase):
    def test_batch_results_in_case_order(self) -> None:
        self.assertEqual(
            prefix_many([([1, 2, 3],), ([],), ([-3, 0, 5],)]),
            [[1, 3, 6], [], [-3, -3, 2]],
        )

    def test_empty_batch(self) -> None:
        self.assertEqual(prefix_many([]), [])

    def test_cases_and_shared_arguments_are_unchanged(self) -> None:
        items = [2, -1, 4]
        cases = [(items,), (items,)]
        original_cases = cases.copy()
        result = prefix_many(cases)
        self.assertEqual(cases, original_cases)
        self.assertIs(cases[0], original_cases[0])
        self.assertIs(cases[1], original_cases[1])
        self.assertIs(cases[0][0], items)
        self.assertEqual(items, [2, -1, 4])
        self.assertEqual(result, [[2, 1, 5], [2, 1, 5]])
        result[0].append(99)
        self.assertEqual(result[1], [2, 1, 5])
        self.assertEqual(items, [2, -1, 4])

    def test_first_exception_is_propagated_unchanged_and_stops_batch(self) -> None:
        error = ValueError("first failure")
        cases = [([1],), ([2],), ([3],)]
        with patch("solution.prefix", side_effect=[[1], error, RuntimeError()]) as mock:
            with self.assertRaises(ValueError) as caught:
                prefix_many(cases)
        self.assertIs(caught.exception, error)
        self.assertEqual(mock.call_args_list, [call([1]), call([2])])
        self.assertEqual(cases, [([1],), ([2],), ([3],)])

    def test_invalid_positional_argument_counts_raise(self) -> None:
        for case in [(), ([1], [2])]:
            with self.subTest(case=case):
                with self.assertRaises(TypeError):
                    prefix_many([case])


if __name__ == "__main__":
    unittest.main()
