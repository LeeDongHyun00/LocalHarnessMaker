"""Regression coverage for the public balanced API."""

import unittest
from unittest.mock import call, patch

from solution import balanced, balanced_many


class BalancedTests(unittest.TestCase):
    def test_empty_and_non_bracket_text(self) -> None:
        for text in ("", "hello world", "123 + café\n🙂"):
            with self.subTest(text=text):
                self.assertIs(balanced(text), True)

    def test_matching_pairs_and_nested_brackets(self) -> None:
        for text in ("()", "[]", "{}", "()[]{}", "{[()]}", "([]{})"):
            with self.subTest(text=text):
                self.assertIs(balanced(text), True)

    def test_unmatched_opening_brackets(self) -> None:
        for text in ("(", "[", "{", "([]", "()[]{"):
            with self.subTest(text=text):
                self.assertIs(balanced(text), False)

    def test_unmatched_closing_brackets(self) -> None:
        for text in (")", "]", "}", ")(", "[]}"):
            with self.subTest(text=text):
                self.assertIs(balanced(text), False)

    def test_mismatched_and_crossed_nesting(self) -> None:
        for text in ("(]", "{)", "[}", "([)]", "{[}]"):
            with self.subTest(text=text):
                self.assertIs(balanced(text), False)

    def test_other_characters_are_ignored(self) -> None:
        self.assertIs(balanced("call(a[0], {'key': (value)})"), True)
        self.assertIs(balanced("before [middle) after"), False)


class BalancedManyTests(unittest.TestCase):
    def test_empty_cases(self) -> None:
        self.assertEqual(balanced_many([]), [])

    def test_results_follow_case_order(self) -> None:
        self.assertEqual(
            balanced_many([("([)]",), ("",), ("{[()]}",), ("(",)]),
            [False, True, True, False],
        )

    def test_cases_and_mutable_arguments_are_unchanged(self) -> None:
        brackets = ["(", "[", "]", ")"]
        unclosed = ["{"]
        cases = [(brackets,), (unclosed,)]
        original_cases = cases.copy()
        original_arguments = [brackets.copy(), unclosed.copy()]
        self.assertEqual(balanced_many(cases), [True, False])
        self.assertEqual(cases, original_cases)
        for case, original_case, original_argument in zip(
            cases, original_cases, original_arguments
        ):
            self.assertIs(case, original_case)
            self.assertIs(case[0], original_case[0])
            self.assertEqual(case[0], original_argument)

    def test_invalid_argument_counts_propagate(self) -> None:
        for case in ((), ("()", "[]")):
            with self.subTest(case=case):
                with self.assertRaises(TypeError):
                    balanced_many([case])

    def test_positional_forwarding_and_first_exception_identity(self) -> None:
        error = RuntimeError("first failure")
        cases = [("()",), ("[]", "{}"), ("later",)]
        with patch("solution.balanced", side_effect=[True, error, False]) as mock:
            with self.assertRaises(RuntimeError) as caught:
                balanced_many(cases)
        self.assertIs(caught.exception, error)
        self.assertEqual(mock.call_args_list, [call("()"), call("[]", "{}")])


if __name__ == "__main__":
    unittest.main()
