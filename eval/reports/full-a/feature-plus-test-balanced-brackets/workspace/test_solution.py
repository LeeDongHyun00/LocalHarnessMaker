"""Tests for the public bracket-balancing API."""

import unittest

from solution import balanced


class BalancedTests(unittest.TestCase):
    def test_balanced_brackets(self) -> None:
        for text in ("()", "[]", "{}", "([]{})", "{[()]}", "()[]{}"):
            with self.subTest(text=text):
                self.assertIs(balanced(text), True)

    def test_unbalanced_brackets(self) -> None:
        for text in ("([)]", "(]", "{)", "(()", "())", "][]", "{}["):
            with self.subTest(text=text):
                self.assertIs(balanced(text), False)

    def test_single_bracket_boundaries(self) -> None:
        for text in "()[]{}":
            with self.subTest(text=text):
                self.assertIs(balanced(text), False)

    def test_empty_text(self) -> None:
        self.assertIs(balanced(""), True)

    def test_other_characters_are_ignored(self) -> None:
        for text in ("plain text", " \t\n", "a(b[c]{d})e", "한글 🙂 <>"):
            with self.subTest(text=text):
                self.assertIs(balanced(text), True)
        self.assertIs(balanced("a(b]c"), False)


if __name__ == "__main__":
    unittest.main()
