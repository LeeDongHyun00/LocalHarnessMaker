"""Regression coverage for the public last_index API."""

import unittest
from unittest.mock import call, patch

from solution import last_index, last_index_many


class LastIndexTests(unittest.TestCase):
    def test_returns_last_duplicate_index(self) -> None:
        self.assertEqual(last_index(["a", "b", "a", "b"], "a"), 2)

    def test_absent_target_returns_none(self) -> None:
        self.assertIsNone(last_index(["a", "b"], "c"))

    def test_empty_input_returns_none(self) -> None:
        self.assertIsNone(last_index([], "a"))

    def test_matching_is_case_sensitive(self) -> None:
        self.assertEqual(last_index(["a", "A"], "a"), 0)
        self.assertIsNone(last_index(["A"], "a"))

    def test_boundary_indices(self) -> None:
        self.assertEqual(last_index(["a"], "a"), 0)
        self.assertEqual(last_index(["a", "b"], "b"), 1)

    def test_input_is_not_mutated(self) -> None:
        items = ["a", "b", "a"]
        original = items.copy()
        self.assertEqual(last_index(items, "a"), 2)
        self.assertEqual(items, original)
        self.assertIsNone(last_index(items, "missing"))
        self.assertEqual(items, original)


class LastIndexManyTests(unittest.TestCase):
    def test_results_follow_case_order(self) -> None:
        self.assertEqual(
            last_index_many([
                (["a", "b", "a"], "a"),
                (["a"], "missing"),
                ([], "a"),
                (["A", "a"], "A"),
                (["b"], "b"),
            ]),
            [2, None, None, 0, 0],
        )

    def test_empty_batch_returns_empty_list(self) -> None:
        self.assertEqual(last_index_many([]), [])

    def test_cases_and_shared_arguments_are_not_mutated(self) -> None:
        items = ["a", "b", "a"]
        cases = [(items, "a"), (items, "missing")]
        original_cases = cases.copy()
        original_items = items.copy()
        self.assertEqual(last_index_many(cases), [2, None])
        self.assertEqual(cases, original_cases)
        self.assertEqual(items, original_items)
        for case, original in zip(cases, original_cases):
            self.assertIs(case, original)
            self.assertIs(case[0], items)

    def test_first_exception_is_unchanged_and_stops_batch(self) -> None:
        first_error = RuntimeError("first failure")
        later_error = ValueError("later failure")
        cases = [(["a"], "a"), ([], "b"), (["c"], "c")]
        original_cases = cases.copy()
        with patch("solution.last_index", side_effect=[0, first_error, later_error]) as single:
            with self.assertRaises(RuntimeError) as raised:
                last_index_many(cases)
        self.assertIs(raised.exception, first_error)
        self.assertEqual(single.call_args_list, [call(*cases[0]), call(*cases[1])])
        self.assertEqual(cases, original_cases)

    def test_invalid_positional_arguments_propagate_type_error(self) -> None:
        with self.assertRaises(TypeError):
            last_index_many([(["a"],)])


if __name__ == "__main__":
    unittest.main()
