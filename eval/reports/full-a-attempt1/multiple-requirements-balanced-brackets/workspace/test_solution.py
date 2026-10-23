"""Regression tests for the public balanced API."""

import unittest

from solution import balanced


class BalancedTests(unittest.TestCase):
    def test_balanced_brackets(self) -> None:
        for text in ('()', '[]', '{}', '([]{})', '{[()]}', '()[]{}'):
            with self.subTest(text=text):
                self.assertIs(balanced(text), True)

    def test_unmatched_brackets(self) -> None:
        for text in ('(', ')', '[', ']', '{', '}', '(()', '())', '[]{}('):
            with self.subTest(text=text):
                self.assertIs(balanced(text), False)

    def test_incorrect_order_and_mismatched_types(self) -> None:
        for text in (')(', '][', '}{', '(]', '[)', '{]', '([)]', '{(})'):
            with self.subTest(text=text):
                self.assertIs(balanced(text), False)

    def test_empty_and_non_bracket_characters(self) -> None:
        for text in ('', 'plain text', 'a{b[c(d)e]f}g', '你好 😀\n', '<>'):
            with self.subTest(text=text):
                self.assertIs(balanced(text), True)
        self.assertIs(balanced('words [ more words'), False)

    def test_preserves_input_values_and_collection_order(self) -> None:
        texts = ['([)]', 'a(b)c', '', '}{', '{[()]}']
        original = texts.copy()
        self.assertEqual([balanced(text) for text in texts],
                         [False, True, True, False, True])
        self.assertEqual(texts, original)


if __name__ == '__main__':
    unittest.main()
