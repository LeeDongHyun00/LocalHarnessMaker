"""Regression tests for the public merge API."""

import unittest
from copy import deepcopy
from unittest.mock import call, patch

from solution import merge, merge_many


class MergeTests(unittest.TestCase):
    def test_union_and_shared_counts(self) -> None:
        self.assertEqual(
            merge({"left": 2, "shared": 3}, {"right": 4, "shared": 5}),
            {"left": 2, "shared": 8, "right": 4},
        )

    def test_zero_and_negative_totals_are_preserved(self) -> None:
        self.assertEqual(
            merge(
                {"cancel": 3, "negative": -5, "left_zero": 0},
                {"cancel": -3, "negative": 2, "right_zero": 0, "right_negative": -4},
            ),
            {"cancel": 0, "negative": -3, "left_zero": 0,
             "right_zero": 0, "right_negative": -4},
        )

    def test_inputs_are_unchanged_and_result_is_independent(self) -> None:
        left = {"left": 1, "shared": 2}
        right = {"right": -1, "shared": 3}
        left_before = left.copy()
        right_before = right.copy()
        result = merge(left, right)
        self.assertEqual(left, left_before)
        self.assertEqual(right, right_before)
        self.assertIsNot(result, left)
        self.assertIsNot(result, right)
        result["shared"] = 99
        self.assertEqual(left, left_before)
        self.assertEqual(right, right_before)

    def test_empty_inputs(self) -> None:
        self.assertEqual(merge({}, {}), {})
        self.assertEqual(merge({"a": -2}, {}), {"a": -2})
        self.assertEqual(merge({}, {"a": 0}), {"a": 0})

    def test_same_dictionary_as_both_inputs(self) -> None:
        counts = {"positive": 2, "zero": 0, "negative": -3}
        self.assertEqual(
            merge(counts, counts), {"positive": 4, "zero": 0, "negative": -6}
        )
        self.assertEqual(counts, {"positive": 2, "zero": 0, "negative": -3})

    def test_batch_preserves_order_and_inputs(self) -> None:
        shared = {"shared": 2}
        cases = [({"a": 1}, {"a": 3}), (shared, shared), ({}, {"z": -1})]
        before = deepcopy(cases)
        original_cases = list(cases)
        original_arguments = [tuple(case) for case in cases]

        results = merge_many(cases)

        self.assertEqual(results, [{"a": 4}, {"shared": 4}, {"z": -1}])
        self.assertEqual(cases, before)
        for case, original_case, arguments in zip(cases, original_cases, original_arguments):
            self.assertIs(case, original_case)
            for argument, original_argument in zip(case, arguments):
                self.assertIs(argument, original_argument)
        results[1]["shared"] = 99
        self.assertEqual(cases, before)

    def test_batch_empty(self) -> None:
        with patch("solution.merge") as merge_call:
            self.assertEqual(merge_many([]), [])
        merge_call.assert_not_called()

    def test_batch_propagates_first_exception_unchanged(self) -> None:
        first_error = ValueError("first failure")
        later_error = RuntimeError("later failure")
        cases = [({"a": 1}, {}), ({"b": 2}, {}), ({"c": 3}, {})]
        before = deepcopy(cases)
        with patch("solution.merge", side_effect=[{"a": 1}, first_error, later_error]) as merge_call:
            with self.assertRaises(ValueError) as raised:
                merge_many(cases)
        self.assertIs(raised.exception, first_error)
        self.assertEqual(merge_call.call_args_list, [call(*cases[0]), call(*cases[1])])
        self.assertEqual(cases, before)

    def test_batch_forwards_positional_argument_count(self) -> None:
        with self.assertRaises(TypeError):
            merge_many([({},)])


if __name__ == "__main__":
    unittest.main()
