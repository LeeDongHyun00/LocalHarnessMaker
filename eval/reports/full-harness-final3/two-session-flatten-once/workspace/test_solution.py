"""Regression tests for the public flatten API."""

import unittest
from copy import deepcopy
from unittest.mock import call, patch

from solution import flatten, flatten_many


class FlattenTests(unittest.TestCase):
    def test_preserves_order_and_duplicates(self) -> None:
        self.assertEqual(flatten([[3, 1], [3], [2, 0]]), [3, 1, 3, 2, 0])

    def test_ignores_empty_inner_lists(self) -> None:
        self.assertEqual(flatten([[], [1], [], [2, 3], []]), [1, 2, 3])
        self.assertEqual(flatten([[], []]), [])

    def test_empty_input_returns_new_list(self) -> None:
        items: list[list[int]] = []
        result = flatten(items)
        self.assertEqual(result, [])
        self.assertIsNot(result, items)

    def test_flattens_exactly_one_level(self) -> None:
        nested = [1, 2]
        items = [[nested], [], [[3]]]
        before = deepcopy(items)
        result = flatten(items)
        self.assertEqual(result, [[1, 2], [3]])
        self.assertIs(result[0], nested)
        self.assertEqual(items, before)

    def test_returns_new_list_without_mutating_inputs(self) -> None:
        first = [1, 2]
        second = [3]
        items = [first, second]
        before = deepcopy(items)
        result = flatten(items)
        self.assertEqual(items, before)
        self.assertIs(items[0], first)
        self.assertIs(items[1], second)
        self.assertIsNot(result, items)
        self.assertIsNot(result, first)
        self.assertIsNot(result, second)
        result.append(4)
        self.assertEqual(items, before)


class FlattenManyTests(unittest.TestCase):
    def test_batch_preserves_case_order(self) -> None:
        cases = [([[3], [1, 3]],), ([[], [2]],), ([[]],)]
        self.assertEqual(flatten_many(cases), [[3, 1, 3], [2], []])

    def test_batch_empty_input(self) -> None:
        cases = []
        with patch("solution.flatten") as single:
            result = flatten_many(cases)
        self.assertEqual(result, [])
        self.assertIsNot(result, cases)
        single.assert_not_called()

    def test_batch_does_not_mutate_cases_or_arguments(self) -> None:
        nested = [1, 2]
        inner = [nested]
        items = [inner, [3]]
        case = (items,)
        cases = [case, (items,)]
        before = deepcopy(cases)
        result = flatten_many(cases)
        self.assertEqual(cases, before)
        self.assertIs(cases[0], case)
        self.assertIs(cases[0][0], items)
        self.assertIs(items[0], inner)
        self.assertIs(inner[0], nested)
        self.assertIs(result[0][0], nested)
        self.assertIsNot(result[0], result[1])
        result[0].append(4)
        self.assertEqual(cases, before)

    def test_batch_propagates_first_exception_unchanged(self) -> None:
        first_error = ValueError("first failure")
        later_error = RuntimeError("later failure")
        cases = [([[1]],), ([[2]],), ([[3]],)]
        before = deepcopy(cases)
        with patch("solution.flatten", side_effect=[[1], first_error, later_error]) as single:
            with self.assertRaises(ValueError) as caught:
                flatten_many(cases)
        self.assertIs(caught.exception, first_error)
        self.assertEqual(single.call_args_list, [call(*cases[0]), call(*cases[1])])
        self.assertEqual(cases, before)

    def test_batch_expands_positional_arguments(self) -> None:
        cases = [(), ("first", "second")]
        with patch("solution.flatten", side_effect=[[], [1]]) as single:
            self.assertEqual(flatten_many(cases), [[], [1]])
        self.assertEqual(single.call_args_list, [call(), call("first", "second")])


if __name__ == "__main__":
    unittest.main()
