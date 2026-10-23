"""Tests for the public bracket-balancing API."""

import unittest

from solution import balanced


class BalancedTests(unittest.TestCase):
    def test_balanced_brackets(self) -> None:
        for text in ("()", "[]", "{}", "([]{})", "{[()]}", "()[]{}"):
            with self.subTest(text=text):
                self.assertIs(balanced(text), True)

    def test_unmatched_brackets(self) -> None:
        for text in ("(", "[", "{", ")", "]", "}", "(()", "())", ")("):
            with self.subTest(text=text):
                self.assertIs(balanced(text), False)

    def test_incorrect_nesting(self) -> None:
        for text in ("(]", "[}", "{)", "([)]", "{[(])}"):
            with self.subTest(text=text):
                self.assertIs(balanced(text), False)

    def test_empty_and_non_bracket_text(self) -> None:
        for text in ("", "hello", " \t\n", "한글 123 !", "a(b[c]{d})e"):
            with self.subTest(text=text):
                self.assertIs(balanced(text), True)
        for text in ("text (more", "text ] more", "a[b)c"):
            with self.subTest(text=text):
                self.assertIs(balanced(text), False)


if __name__ == "__main__":
    unittest.main()
