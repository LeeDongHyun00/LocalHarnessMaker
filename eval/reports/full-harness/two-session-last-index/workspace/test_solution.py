"""Regression tests for the public last_index and batch APIs."""

import unittest
from unittest import TestCase
from unittest.mock import call, patch

from solution import last_index, last_index_many


class LastIndexTests(TestCase):
    def test_repeated_target_returns_last_index(self) -> None:
        self.assertEqual(last_index(["a", "b", "a", "c", "a"], "a"), 4)

    def test_absent_target_returns_none(self) -> None:
        self.assertIsNone(last_index(["a", "b"], "c"))

    def test_empty_input_returns_none(self) -> None:
        self.assertIsNone(last_index([], "a"))

    def test_matching_is_case_sensitive(self) -> None:
        self.assertEqual(last_index(["a", "A", "A"], "a"), 0)
        self.assertIsNone(last_index(["A"], "a"))

    def test_single_match_at_zero(self) -> None:
        self.assertEqual(last_index(["a"], "a"), 0)

    def test_input_is_not_mutated(self) -> None:
        items = ["b", "a", "b", "c"]
        original = items.copy()
        self.assertEqual(last_index(items, "b"), 2)
        self.assertEqual(items, original)
        self.assertIsNone(last_index(items, "missing"))
        self.assertEqual(items, original)

    def test_batch_returns_results_in_case_order(self) -> None:
        cases = [(["a", "b", "a"], "a"), ([], "a"), (["b"], "a"), (["A"], "A")]
        self.assertEqual(last_index_many(cases), [2, None, None, 0])

    def test_batch_empty_returns_empty_list(self) -> None:
        self.assertEqual(last_index_many([]), [])

    def test_batch_does_not_mutate_cases_or_arguments(self) -> None:
        items = ["b", "a", "b", "c"]
        cases = [(items, "b"), (items, "missing")]
        original_cases = cases.copy()
        original_items = items.copy()
        self.assertEqual(last_index_many(cases), [2, None])
        self.assertEqual(cases, original_cases)
        self.assertEqual(items, original_items)
        for actual, original in zip(cases, original_cases):
            self.assertIs(actual, original)
            self.assertIs(actual[0], items)

    def test_batch_propagates_first_exception_unchanged(self) -> None:
        cases = [(["a"], "a"), (["b"], "b"), (["c"], "c")]
        error = ValueError("first failure")
        with patch("solution.last_index", side_effect=[0, error, RuntimeError("later failure")]) as single:
            with self.assertRaises(ValueError) as caught:
                last_index_many(cases)
        self.assertIs(caught.exception, error)
        self.assertEqual(single.call_args_list, [call(*cases[0]), call(*cases[1])])

    def test_batch_invalid_argument_count_propagates(self) -> None:
        with self.assertRaises(TypeError):
            last_index_many([(["a"],)])


if __name__ == "__main__":
    unittest.main()
