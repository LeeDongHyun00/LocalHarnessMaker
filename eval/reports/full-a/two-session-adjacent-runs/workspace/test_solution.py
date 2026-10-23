"""Regression coverage for the public runs API."""

import unittest
from unittest.mock import call, patch

from solution import runs, runs_many


class RunsTests(unittest.TestCase):
    def test_empty_input(self) -> None:
        self.assertEqual(runs([]), [])

    def test_single_value(self) -> None:
        self.assertEqual(runs(["a"]), [("a", 1)])

    def test_adjacent_equal_values_are_counted(self) -> None:
        self.assertEqual(
            runs(["a", "a", "b", "b", "b", "c"]),
            [("a", 2), ("b", 3), ("c", 1)],
        )

    def test_nonadjacent_equal_values_remain_separate(self) -> None:
        self.assertEqual(
            runs(["a", "b", "a", "a"]),
            [("a", 1), ("b", 1), ("a", 2)],
        )

    def test_empty_strings_and_unicode(self) -> None:
        self.assertEqual(
            runs(["", "", "안녕", "안녕", ""]),
            [("", 2), ("안녕", 2), ("", 1)],
        )

    def test_input_is_not_mutated(self) -> None:
        items = ["a", "a", "b", "a"]
        original = items.copy()
        result = runs(items)
        self.assertEqual(items, original)
        result.append(("extra", 1))
        self.assertEqual(items, original)


class RunsManyTests(unittest.TestCase):
    def test_empty_cases(self) -> None:
        self.assertEqual(runs_many([]), [])

    def test_results_follow_case_order(self) -> None:
        self.assertEqual(
            runs_many([(["a", "a", "b"],), ([],), (["안녕", "안녕"],)]),
            [[("a", 2), ("b", 1)], [], [("안녕", 2)]],
        )

    def test_cases_and_arguments_are_not_mutated(self) -> None:
        items = ["a", "a", "b"]
        cases = [(items,), (items,)]
        original_cases = cases.copy()
        original_items = items.copy()
        results = runs_many(cases)
        self.assertEqual(cases, original_cases)
        self.assertIs(cases[0], original_cases[0])
        self.assertIs(cases[0][0], items)
        self.assertEqual(items, original_items)
        results[0].append(("extra", 1))
        self.assertEqual(results[1], [("a", 2), ("b", 1)])
        self.assertEqual(items, original_items)

    def test_first_exception_is_propagated_unchanged(self) -> None:
        failure = ValueError("first failure")
        later_failure = RuntimeError("must not be reached")
        with patch("solution.runs", side_effect=[[], failure, later_failure]) as mocked:
            with self.assertRaises(ValueError) as caught:
                runs_many([(["a"],), (["b"],), (["c"],)])
        self.assertIs(caught.exception, failure)
        self.assertEqual(mocked.call_args_list, [call(["a"]), call(["b"])])

    def test_invalid_positional_arguments_propagate_type_error(self) -> None:
        for case in [(), (["a"], ["b"])]:
            with self.subTest(case=case):
                with self.assertRaises(TypeError):
                    runs_many([case])


if __name__ == "__main__":
    unittest.main()
