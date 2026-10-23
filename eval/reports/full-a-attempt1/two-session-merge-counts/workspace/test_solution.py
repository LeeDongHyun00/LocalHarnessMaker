"""Regression coverage for the public merge API."""

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
                {"cancelled": 3, "negative": -4, "left_zero": 0},
                {"cancelled": -3, "negative": 1, "right_zero": 0, "debt": -2},
            ),
            {"cancelled": 0, "negative": -3, "left_zero": 0, "right_zero": 0, "debt": -2},
        )

    def test_inputs_unchanged_and_result_independent(self) -> None:
        left = {"shared": 2, "left": -1}
        right = {"shared": -2, "right": 0}
        result = merge(left, right)
        self.assertEqual(left, {"shared": 2, "left": -1})
        self.assertEqual(right, {"shared": -2, "right": 0})
        self.assertIsNot(result, left)
        self.assertIsNot(result, right)
        result["shared"] = 99
        self.assertEqual(left["shared"], 2)
        self.assertEqual(right["shared"], -2)

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
        counts = {"positive": 2, "zero": 0, "negative": -3}
        self.assertEqual(merge(counts, counts), {"positive": 4, "zero": 0, "negative": -6})
        self.assertEqual(counts, {"positive": 2, "zero": 0, "negative": -3})


class MergeManyTests(unittest.TestCase):
    def test_batch_order_and_inputs_unchanged(self) -> None:
        shared = {"a": 2, "zero": 0}
        right = {"a": -2, "negative": -3}
        cases = [(shared, right), ({}, shared), (shared, shared)]
        original_cases = cases.copy()
        results = merge_many(cases)
        self.assertEqual(
            results,
            [
                {"a": 0, "zero": 0, "negative": -3},
                {"a": 2, "zero": 0},
                {"a": 4, "zero": 0},
            ],
        )
        self.assertEqual(cases, original_cases)
        for case, original in zip(cases, original_cases):
            self.assertIs(case, original)
        self.assertEqual(shared, {"a": 2, "zero": 0})
        self.assertEqual(right, {"a": -2, "negative": -3})
        self.assertEqual(cases[1][0], {})
        results[0]["a"] = 99
        self.assertEqual(results[1]["a"], 2)
        self.assertEqual(shared["a"], 2)
        self.assertEqual(right["a"], -2)

    def test_empty_batch(self) -> None:
        cases = []
        self.assertEqual(merge_many(cases), [])
        self.assertEqual(cases, [])

    def test_first_exception_propagates_unchanged_and_stops_batch(self) -> None:
        cases = [({"a": 1}, {}), ({"b": 2}, {}), ({"c": 3}, {})]
        error = RuntimeError("merge failed")
        with patch("solution.merge", side_effect=[{"a": 1}, error, {"c": 3}]) as mock_merge:
            with self.assertRaises(RuntimeError) as raised:
                merge_many(cases)
        self.assertIs(raised.exception, error)
        self.assertEqual(mock_merge.call_args_list, [call(*cases[0]), call(*cases[1])])

    def test_invalid_argument_count_raises(self) -> None:
        with self.assertRaises(TypeError):
            merge_many([({},)])


if __name__ == "__main__":
    unittest.main()
