"""Regression tests for the public flatten API."""

import unittest
from unittest.mock import call, patch

from solution import flatten, flatten_many


class FlattenTests(unittest.TestCase):
    def test_preserves_order_and_duplicates(self) -> None:
        self.assertEqual(flatten([[3, 1], [1, -2], [0]]), [3, 1, 1, -2, 0])

    def test_ignores_empty_inner_lists(self) -> None:
        self.assertEqual(flatten([[], [1], [], [2, 3], []]), [1, 2, 3])

    def test_empty_inputs_return_new_lists(self) -> None:
        items: list[list[int]] = []
        first = flatten(items)
        second = flatten(items)
        self.assertEqual(first, [])
        self.assertIsNot(first, items)
        self.assertIsNot(first, second)
        self.assertEqual(flatten([[], []]), [])

    def test_does_not_mutate_or_reuse_input_lists(self) -> None:
        inner = [1, 2]
        items = [inner, [], inner]
        original_inners = items.copy()
        result = flatten(items)

        self.assertEqual(result, [1, 2, 1, 2])
        self.assertEqual(items, [[1, 2], [], [1, 2]])
        for actual, original in zip(items, original_inners):
            self.assertIs(actual, original)
            self.assertIsNot(result, actual)
        self.assertIsNot(result, items)

        result.append(9)
        self.assertEqual(items, [[1, 2], [], [1, 2]])
        inner.append(3)
        self.assertEqual(result, [1, 2, 1, 2, 9])


class FlattenManyTests(unittest.TestCase):
    def test_returns_results_in_case_order(self) -> None:
        cases = [([[3, 1], [], [1]],), ([],), ([[2], [-1, 0]],)]
        self.assertEqual(flatten_many(cases), [[3, 1, 1], [], [2, -1, 0]])

    def test_empty_cases_return_fresh_lists(self) -> None:
        cases = []
        first = flatten_many(cases)
        second = flatten_many(cases)
        self.assertEqual(first, [])
        self.assertIsNot(first, cases)
        self.assertIsNot(first, second)
        self.assertEqual(cases, [])

    def test_preserves_cases_and_shared_arguments(self) -> None:
        inner = [1, 2]
        items = [inner, [], inner]
        case = (items,)
        cases = [case, case]
        results = flatten_many(cases)

        self.assertEqual(results, [[1, 2, 1, 2], [1, 2, 1, 2]])
        self.assertEqual(cases, [([[1, 2], [], [1, 2]],)] * 2)
        self.assertIs(cases[0], case)
        self.assertIs(cases[1], case)
        self.assertIs(case[0], items)
        self.assertIs(items[0], inner)
        self.assertIs(items[2], inner)
        self.assertIsNot(results[0], results[1])
        results[0].append(9)
        self.assertEqual(results[1], [1, 2, 1, 2])
        self.assertEqual(items, [[1, 2], [], [1, 2]])

    def test_propagates_first_exception_unchanged_and_stops(self) -> None:
        error = ValueError("first failure")
        cases = [([[1]],), ([[2]],), ([[3]],)]
        with patch("solution.flatten", side_effect=[[1], error, RuntimeError()]) as mocked:
            with self.assertRaises(ValueError) as raised:
                flatten_many(cases)
        self.assertIs(raised.exception, error)
        self.assertEqual(mocked.call_args_list, [call([[1]]), call([[2]])])
        self.assertEqual(cases, [([[1]],), ([[2]],), ([[3]],)])

    def test_invalid_positional_arguments_raise_type_error(self) -> None:
        for case in [(), ([], []), (None,)]:
            with self.subTest(case=case):
                with self.assertRaises(TypeError):
                    flatten_many([case])


if __name__ == "__main__":
    unittest.main()
