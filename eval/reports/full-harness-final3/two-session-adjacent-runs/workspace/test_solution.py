"""Regression tests for the public runs API."""

import unittest
from unittest.mock import call, patch

from solution import runs, runs_many


class RunsTests(unittest.TestCase):
    def test_empty_input(self) -> None:
        self.assertEqual(runs([]), [])

    def test_adjacent_equal_values_are_counted(self) -> None:
        self.assertEqual(
            runs(["a", "a", "b", "b", "b", "c"]),
            [("a", 2), ("b", 3), ("c", 1)],
        )

    def test_nonadjacent_equal_values_remain_separate(self) -> None:
        self.assertEqual(runs(["a", "b", "a"]), [("a", 1), ("b", 1), ("a", 1)])

    def test_single_value(self) -> None:
        self.assertEqual(runs(["hello"]), [("hello", 1)])

    def test_empty_and_unicode_strings(self) -> None:
        self.assertEqual(
            runs(["", "", "한", "한", ""]), [("", 2), ("한", 2), ("", 1)]
        )

    def test_input_is_not_mutated(self) -> None:
        items = ["a", "a", "b", "a"]
        original = items.copy()
        self.assertEqual(runs(items), [("a", 2), ("b", 1), ("a", 1)])
        self.assertEqual(items, original)

    def test_runs_many_preserves_order_and_inputs(self) -> None:
        items = ["a", "a", "b"]
        cases = [(items,), ([],), (["한", "한"],), (items,)]
        original_cases = cases.copy()
        original_arguments = [case[0].copy() for case in cases]
        self.assertEqual(
            runs_many(cases),
            [[("a", 2), ("b", 1)], [], [("한", 2)], [("a", 2), ("b", 1)]],
        )
        self.assertEqual(cases, original_cases)
        for case, original_case, original_argument in zip(
            cases, original_cases, original_arguments
        ):
            self.assertIs(case, original_case)
            self.assertIs(case[0], original_case[0])
            self.assertEqual(case[0], original_argument)

    def test_runs_many_empty(self) -> None:
        with patch("solution.runs") as mocked_runs:
            self.assertEqual(runs_many([]), [])
            mocked_runs.assert_not_called()

    def test_runs_many_unpacks_positional_arguments(self) -> None:
        with patch("solution.runs", side_effect=["first", "second"]) as mocked_runs:
            self.assertEqual(runs_many([(1, 2), (3,)]), ["first", "second"])
            self.assertEqual(mocked_runs.call_args_list, [call(1, 2), call(3)])

    def test_runs_many_propagates_first_exception_unchanged(self) -> None:
        error = ValueError("failed case")
        cases = [(["a"],), (["b"],), (["c"],)]
        with patch("solution.runs", side_effect=[[], error]) as mocked_runs:
            with self.assertRaises(ValueError) as caught:
                runs_many(cases)
            self.assertIs(caught.exception, error)
            self.assertEqual(mocked_runs.call_args_list, [call(["a"]), call(["b"])])


if __name__ == "__main__":
    unittest.main()
