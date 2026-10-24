"""Regression tests for the public bracket-checking API."""

import unittest
from unittest.mock import call, patch

from solution import balanced, balanced_many


class BalancedTests(unittest.TestCase):
    def test_empty_and_non_bracket_text(self) -> None:
        for text in ("", "hello world", "123 + café\n"):
            with self.subTest(text=text):
                self.assertIs(balanced(text), True)

    def test_balanced_pairs_and_nesting(self) -> None:
        for text in ("()", "[]", "{}", "()[]{}", "{[()]}", "(()[{}])"):
            with self.subTest(text=text):
                self.assertIs(balanced(text), True)

    def test_mismatched_and_crossed_pairs(self) -> None:
        for text in ("(]", "[}", "{)", "([)]", "{[(])}"):
            with self.subTest(text=text):
                self.assertIs(balanced(text), False)

    def test_unmatched_openers_and_closers(self) -> None:
        for text in ("(", "[", "{", ")", "]", "}", ")(", "([]", "[]}"):
            with self.subTest(text=text):
                self.assertIs(balanced(text), False)

    def test_other_characters_are_ignored(self) -> None:
        self.assertIs(balanced("call(x[2], {key: 'value'})\n"), True)
        self.assertIs(balanced("text (more [text) here]"), False)
        self.assertIs(balanced("'('"), False)


class BalancedManyTests(unittest.TestCase):
    def test_many_results_in_order_without_mutation(self) -> None:
        cases = [("{[()]}",), ("([)]",), ("",), ("(",), ("plain text",)]
        original_cases = cases.copy()
        expected = [balanced(*arguments) for arguments in cases]

        self.assertEqual(balanced_many(cases), expected)
        self.assertEqual(cases, original_cases)
        for actual, original in zip(cases, original_cases):
            self.assertIs(actual, original)

    def test_many_empty_does_not_call_balanced(self) -> None:
        with patch("solution.balanced") as single:
            self.assertEqual(balanced_many([]), [])
            single.assert_not_called()

    def test_many_forwards_positional_arguments_once_in_order(self) -> None:
        argument = []
        cases = [(), (argument,), ("a", "b")]
        with patch("solution.balanced", side_effect=[True, False, True]) as single:
            self.assertEqual(balanced_many(cases), [True, False, True])
            self.assertEqual(single.call_args_list, [call(), call(argument), call("a", "b")])
            self.assertIs(single.call_args_list[1].args[0], argument)
        self.assertEqual(cases, [(), ([],), ("a", "b")])

    def test_many_propagates_first_exception_unchanged_and_stops(self) -> None:
        error = ValueError("sentinel")
        cases = [("()",), ("bad",), ("[]",)]
        original_cases = cases.copy()
        with patch("solution.balanced", side_effect=[True, error, False]) as single:
            with self.assertRaises(ValueError) as raised:
                balanced_many(cases)
            self.assertIs(raised.exception, error)
            self.assertEqual(single.call_args_list, [call("()"), call("bad")])
        self.assertEqual(cases, original_cases)


if __name__ == "__main__":
    unittest.main()
