"""Regression tests for the public unique API."""

import unittest
from unittest.mock import call, patch

from solution import unique, unique_many


class UniqueTests(unittest.TestCase):
    def test_empty_input(self) -> None:
        self.assertEqual(unique([]), [])

    def test_duplicates_keep_first_occurrence_order(self) -> None:
        self.assertEqual(unique(["b", "a", "b", "c", "a"]), ["b", "a", "c"])

    def test_equality_is_case_sensitive(self) -> None:
        self.assertEqual(unique(["Hello", "hello", "Hello", "HELLO"]),
                         ["Hello", "hello", "HELLO"])

    def test_input_is_unchanged_and_result_is_new(self) -> None:
        items = ["b", "a", "b"]
        result = unique(items)
        self.assertEqual(items, ["b", "a", "b"])
        self.assertIsNot(result, items)
        result.append("c")
        self.assertEqual(items, ["b", "a", "b"])

    def test_empty_strings_are_deduplicated(self) -> None:
        self.assertEqual(unique(["", "a", "", "a"]), ["", "a"])

    def test_distinct_input_preserves_order(self) -> None:
        self.assertEqual(unique(["c", "a", "b"]), ["c", "a", "b"])


class UniqueManyTests(unittest.TestCase):
    def test_no_cases(self) -> None:
        self.assertEqual(unique_many([]), [])

    def test_batch_preserves_order_and_inputs(self) -> None:
        first = ["b", "a", "b"]
        second = ["c", "c", "d"]
        cases = [(first,), ([],), (second,), (first,)]
        original_cases = cases.copy()

        results = unique_many(cases)

        self.assertEqual(results, [["b", "a"], [], ["c", "d"], ["b", "a"]])
        self.assertEqual(cases, original_cases)
        for case, original in zip(cases, original_cases):
            self.assertIs(case, original)
        self.assertEqual(first, ["b", "a", "b"])
        self.assertEqual(second, ["c", "c", "d"])
        self.assertIs(cases[0][0], first)
        self.assertIs(cases[2][0], second)
        results[0].append("changed")
        self.assertEqual(results[3], ["b", "a"])
        self.assertEqual(first, ["b", "a", "b"])

    def test_first_exception_propagates_unchanged_and_stops_calls(self) -> None:
        first_error = ValueError("first failure")
        later_error = RuntimeError("later failure")
        cases = [(["a"],), (["b"],), (["c"],)]
        with patch("solution.unique", side_effect=[["a"], first_error, later_error]) as mocked:
            with self.assertRaises(ValueError) as raised:
                unique_many(cases)
        self.assertIs(raised.exception, first_error)
        self.assertEqual(mocked.call_args_list, [call(["a"]), call(["b"])])

    def test_invalid_positional_arguments_propagate_type_error(self) -> None:
        for case in [(), (["a"], ["b"])]:
            with self.subTest(case=case):
                with self.assertRaises(TypeError):
                    unique_many([case])

    def test_underlying_unique_error_leaves_inputs_unchanged(self) -> None:
        items = [["unhashable"]]
        cases = [(["valid"],), (items,), (["later"],)]
        with self.assertRaises(TypeError):
            unique_many(cases)
        self.assertEqual(cases, [(["valid"],), ([["unhashable"]],), (["later"],)])
        self.assertIs(cases[1][0], items)


if __name__ == "__main__":
    unittest.main()
