"""Regression tests for the public unique API."""

import unittest
from unittest.mock import call, patch

from solution import unique, unique_many


class UniqueTests(unittest.TestCase):
    def test_preserves_first_occurrence_order(self) -> None:
        self.assertEqual(
            unique(["pear", "apple", "pear", "banana", "apple"]),
            ["pear", "apple", "banana"],
        )

    def test_empty_input(self) -> None:
        self.assertEqual(unique([]), [])

    def test_case_sensitive_and_empty_strings(self) -> None:
        self.assertEqual(unique(["A", "a", "", "A", "", "a"]), ["A", "a", ""])

    def test_does_not_mutate_input(self) -> None:
        items = ["b", "a", "b"]
        original = items.copy()
        result = unique(items)
        self.assertEqual(items, original)
        self.assertIsNot(result, items)
        self.assertEqual(result, ["b", "a"])

    def test_accepts_iterables(self) -> None:
        self.assertEqual(unique(("b", "a", "b")), ["b", "a"])
        self.assertEqual(unique(item for item in ["c", "b", "c"]), ["c", "b"])

    def test_many_preserves_order_and_inputs(self) -> None:
        first = ["b", "a", "b"]
        second = ["c", "c", "d"]
        cases = [(first,), ([],), (second,)]
        original_cases = cases.copy()
        original_arguments = [case[0].copy() for case in cases]

        self.assertEqual(unique_many(cases), [["b", "a"], [], ["c", "d"]])
        self.assertEqual(cases, original_cases)
        for case, original_case, original_argument in zip(
            cases, original_cases, original_arguments
        ):
            self.assertIs(case, original_case)
            self.assertEqual(case[0], original_argument)

    def test_many_empty(self) -> None:
        self.assertEqual(unique_many([]), [])

    def test_many_forwards_arguments_and_propagates_first_exception(self) -> None:
        error = RuntimeError("first failure")
        cases = [(["a"],), ("first", "second"), ()]
        with patch("solution.unique", side_effect=[["a"], error]) as mocked_unique:
            with self.assertRaises(RuntimeError) as caught:
                unique_many(cases)

        self.assertIs(caught.exception, error)
        self.assertEqual(mocked_unique.call_args_list, [call(["a"]), call("first", "second")])


if __name__ == "__main__":
    unittest.main()
