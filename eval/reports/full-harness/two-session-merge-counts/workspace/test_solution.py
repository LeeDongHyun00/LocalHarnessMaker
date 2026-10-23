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

    def test_preserves_zero_and_negative_totals(self) -> None:
        self.assertEqual(
            merge(
                {"cancel": 3, "negative": -5, "left_zero": 0},
                {"cancel": -3, "negative": 2, "right_zero": 0, "right_negative": -4},
            ),
            {"cancel": 0, "negative": -3, "left_zero": 0,
             "right_zero": 0, "right_negative": -4},
        )

    def test_inputs_unchanged_and_result_independent(self) -> None:
        left = {"left": 2, "shared": 3}
        right = {"right": -4, "shared": -3}
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
        for left, right, expected in (
            ({}, {}, {}),
            ({"a": -1}, {}, {"a": -1}),
            ({}, {"a": 0}, {"a": 0}),
        ):
            with self.subTest(left=left, right=right):
                result = merge(left, right)
                self.assertEqual(result, expected)
                self.assertIsNot(result, left)
                self.assertIsNot(result, right)

    def test_same_dictionary_as_both_inputs(self) -> None:
        counts = {"positive": 3, "zero": 0, "negative": -2}
        self.assertEqual(
            merge(counts, counts),
            {"positive": 6, "zero": 0, "negative": -4},
        )
        self.assertEqual(counts, {"positive": 3, "zero": 0, "negative": -2})

    def test_many_preserves_order_inputs_and_result_independence(self) -> None:
        shared = {"a": 3}
        cases = [(shared, {"a": -3, "b": 0}), ({}, shared), (shared, shared)]
        before = deepcopy(cases)

        results = merge_many(cases)

        self.assertEqual(results, [{"a": 0, "b": 0}, {"a": 3}, {"a": 6}])
        self.assertEqual(cases, before)
        self.assertIs(cases[0][0], shared)
        self.assertIs(cases[1][1], shared)
        self.assertIs(cases[2][0], shared)
        self.assertIs(cases[2][1], shared)
        results[0]["a"] = 99
        self.assertEqual(results[1:], [{"a": 3}, {"a": 6}])
        self.assertEqual(cases, before)

    def test_many_empty(self) -> None:
        with patch("solution.merge") as mocked_merge:
            self.assertEqual(merge_many([]), [])
        mocked_merge.assert_not_called()

    def test_many_propagates_first_exception_unchanged_and_stops(self) -> None:
        cases = [({"a": 1}, {}), ({}, {"b": 2}), ({"c": 3}, {})]
        before = deepcopy(cases)
        error = ValueError("merge failed")
        with patch("solution.merge", side_effect=[{"a": 1}, error, AssertionError()]) as mocked_merge:
            with self.assertRaises(ValueError) as caught:
                merge_many(cases)

        self.assertIs(caught.exception, error)
        self.assertEqual(mocked_merge.call_args_list, [call(*case) for case in cases[:2]])
        self.assertEqual(cases, before)


if __name__ == "__main__":
    unittest.main()
