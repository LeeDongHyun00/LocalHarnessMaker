"""Tests for the public bracket-balancing API."""

import unittest

from solution import balanced


class BalancedTests(unittest.TestCase):
    def test_balanced_brackets(self) -> None:
        for text in ("()", "[]", "{}", "()[]{}", "([{}])", "{[()()]([])}"):
            with self.subTest(text=text):
                self.assertIs(balanced(text), True)

    def test_mismatched_nesting(self) -> None:
        for text in ("(]", "[}", "{)", "([)]", "{[(])}"):
            with self.subTest(text=text):
                self.assertIs(balanced(text), False)

    def test_unmatched_brackets(self) -> None:
        for text in ("(", "[", "{", ")", "]", "}", ")(", "(()", "())", "[]{"):
            with self.subTest(text=text):
                self.assertIs(balanced(text), False)

    def test_ignores_other_characters(self) -> None:
        for text in ("plain text 123 <>", " \t\n", "a(b[c]{d})e", "α[β(γ)]🙂"):
            with self.subTest(text=text):
                self.assertIs(balanced(text), True)
        for text in ("text (more text", "text ] more text", "a[b)c"):
            with self.subTest(text=text):
                self.assertIs(balanced(text), False)

    def test_empty_text(self) -> None:
        self.assertIs(balanced(""), True)


if __name__ == "__main__":
    unittest.main()
