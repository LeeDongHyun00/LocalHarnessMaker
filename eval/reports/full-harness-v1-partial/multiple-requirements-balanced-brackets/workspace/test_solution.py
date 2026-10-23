"""Regression tests for the public balanced API."""

import unittest

from solution import balanced


class BalancedTests(unittest.TestCase):
    def test_empty_and_non_bracket_text(self) -> None:
        for text in ('', 'plain text', '123 + punctuation!'):
            with self.subTest(text=text):
                self.assertTrue(balanced(text))

    def test_valid_nesting_and_adjacent_pairs(self) -> None:
        for text in ('()', '[]', '{}', '([]{})', '{[()]}', '()[]{}',
                     'before {a [b (c)]} after'):
            with self.subTest(text=text):
                self.assertTrue(balanced(text))

    def test_unmatched_brackets(self) -> None:
        for text in ('(', ')', '[', ']', '{', '}', '(()', '())',
                     '[[]', '{}}', 'text [more'):
            with self.subTest(text=text):
                self.assertFalse(balanced(text))

    def test_mismatched_types_and_order(self) -> None:
        for text in (')(', '][', '}{', '(]', '[)', '{]', '([)]', '{[}]'):
            with self.subTest(text=text):
                self.assertFalse(balanced(text))

    def test_input_values_and_collection_order_are_preserved(self) -> None:
        texts = ['{a[b(c)]}', ')(', '', '([)]', 'plain text']
        original = texts.copy()
        self.assertEqual([balanced(text) for text in texts],
                         [True, False, True, False, True])
        self.assertEqual(texts, original)


if __name__ == '__main__':
    unittest.main()
