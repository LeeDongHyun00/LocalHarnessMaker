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

    def test_single_item(self) -> None:
        self.assertEqual(prefix([-8]), [-8])

    def test_preserves_input_and_returns_new_list(self) -> None:
        items = [2, -1, 4]
        result = prefix(items)
        self.assertEqual(items, [2, -1, 4])
        self.assertEqual(result, [2, 1, 5])
        self.assertEqual(len(result), len(items))
        self.assertIsNot(result, items)


class PrefixManyTests(unittest.TestCase):
    def test_batch_results_in_case_order(self) -> None:
        self.assertEqual(
            prefix_many([([1, 2, 3],), ([],), ([-3, 0, 5],), ([8],)]),
            [[1, 3, 6], [], [-3, -3, 2], [8]],
        )

    def test_empty_cases(self) -> None:
        self.assertEqual(prefix_many([]), [])

    def test_preserves_cases_and_shared_arguments(self) -> None:
        items = [2, -1, 4]
        case = (items,)
        cases = [case, case]
        results = prefix_many(cases)
        self.assertEqual(cases, [([2, -1, 4],), ([2, -1, 4],)])
        self.assertIs(cases[0], case)
        self.assertIs(cases[1], case)
        self.assertIs(case[0], items)
        self.assertEqual(results, [[2, 1, 5], [2, 1, 5]])
        self.assertIsNot(results[0], items)
        self.assertIsNot(results[0], results[1])

    def test_propagates_first_exception_unchanged_and_stops(self) -> None:
        error = ValueError("first failure")
        cases = [([1],), ([2],), ([3],)]
        with patch("solution.prefix", side_effect=[[1], error, RuntimeError()]) as mock:
            with self.assertRaises(ValueError) as raised:
                prefix_many(cases)
            self.assertIs(raised.exception, error)
            self.assertEqual(mock.call_args_list, [call([1]), call([2])])
        self.assertEqual(cases, [([1],), ([2],), ([3],)])

    def test_forwards_positional_arguments(self) -> None:
        for case in [(), ([1], [2])]:
            with self.subTest(case=case):
                with self.assertRaises(TypeError):
                    prefix_many([case])


if __name__ == "__main__":
    unittest.main()
