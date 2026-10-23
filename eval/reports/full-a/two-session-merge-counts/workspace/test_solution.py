"""Regression tests for the public merge API."""

import unittest
from unittest.mock import call, patch

from solution import merge, merge_many


class MergeTests(unittest.TestCase):
    def test_union_and_shared_counts(self) -> None:
        self.assertEqual(
            merge({"left": 2, "shared": 3}, {"right": 4, "shared": 5}),
            {"left": 2, "shared": 8, "right": 4},
        )

    def test_preserves_zero_and_negative_totals(self) -> None:
        self.assertEqual(
            merge(
                {"cancel": 3, "negative": -5, "left_zero": 0},
                {"cancel": -3, "negative": 2, "right_zero": 0, "debt": -4},
            ),
            {"cancel": 0, "negative": -3, "left_zero": 0,
             "right_zero": 0, "debt": -4},
        )

    def test_empty_inputs_return_independent_results(self) -> None:
        for left, right in [({}, {}), ({"a": 1}, {}), ({}, {"b": -2})]:
            with self.subTest(left=left, right=right):
                result = merge(left, right)
                self.assertEqual(result, left | right)
                self.assertIsNot(result, left)
                self.assertIsNot(result, right)

    def test_inputs_are_unchanged(self) -> None:
        left = {"shared": 2, "left": 0}
        right = {"shared": -2, "right": -3}
        result = merge(left, right)
        self.assertEqual(left, {"shared": 2, "left": 0})
        self.assertEqual(right, {"shared": -2, "right": -3})
        result["left"] = 99
        result["right"] = 99
        self.assertEqual(left["left"], 0)
        self.assertEqual(right["right"], -3)

    def test_same_dictionary_can_be_both_inputs(self) -> None:
        counts = {"positive": 3, "zero": 0, "negative": -2}
        self.assertEqual(
            merge(counts, counts),
            {"positive": 6, "zero": 0, "negative": -4},
        )
        self.assertEqual(counts, {"positive": 3, "zero": 0, "negative": -2})


class MergeManyTests(unittest.TestCase):
    def test_batch_results_follow_case_order(self) -> None:
        self.assertEqual(
            merge_many([
                ({"shared": 3, "left": 0}, {"shared": -3, "right": -2}),
                ({}, {"second": 4}),
                ({"third": -1}, {}),
            ]),
            [
                {"shared": 0, "left": 0, "right": -2},
                {"second": 4},
                {"third": -1},
            ],
        )

    def test_empty_batch_does_not_call_merge(self) -> None:
        with patch("solution.merge") as merge_mock:
            self.assertEqual(merge_many([]), [])
            merge_mock.assert_not_called()

    def test_batch_and_aliased_arguments_are_unchanged(self) -> None:
        counts = {"positive": 3, "zero": 0, "negative": -2}
        cases = [(counts, counts), (counts, {})]
        original_cases = cases.copy()
        results = merge_many(cases)
        self.assertEqual(cases, original_cases)
        for case, original in zip(cases, original_cases):
            self.assertIs(case, original)
        self.assertEqual(results[0], {"positive": 6, "zero": 0, "negative": -4})
        results[0]["positive"] = 99
        self.assertEqual(results[1], {"positive": 3, "zero": 0, "negative": -2})
        self.assertEqual(counts, {"positive": 3, "zero": 0, "negative": -2})
        self.assertEqual(cases[1][1], {})

    def test_first_exception_is_propagated_unchanged(self) -> None:
        cases = [({}, {}), ({"fail": 1}, {}), ({"later": 2}, {})]
        error = ValueError("merge failed")
        with patch("solution.merge", side_effect=[{}, error, RuntimeError()]) as merge_mock:
            with self.assertRaises(ValueError) as raised:
                merge_many(cases)
            self.assertIs(raised.exception, error)
            self.assertEqual(merge_mock.call_args_list, [call(*cases[0]), call(*cases[1])])
        self.assertEqual(cases, [({}, {}), ({"fail": 1}, {}), ({"later": 2}, {})])

    def test_invalid_positional_arguments_raise_type_error(self) -> None:
        for case in [(), ({},), ({}, {}, {})]:
            with self.subTest(case=case):
                with self.assertRaises(TypeError):
                    merge_many([case])


if __name__ == "__main__":
    unittest.main()
