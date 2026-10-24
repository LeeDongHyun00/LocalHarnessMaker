import unittest

from solution import balanced


class BalancedTests(unittest.TestCase):
    def test_valid_nesting(self):
        for text in ('()', '[]', '{}', '{[()]}', '()[]{}', '([]{})'):
            with self.subTest(text=text):
                self.assertTrue(balanced(text))

    def test_ignored_characters_and_empty_text(self):
        for text in ('', 'plain text', 'a {b [c (d) e] f}!', '\n[你好]\t'):
            with self.subTest(text=text):
                self.assertTrue(balanced(text))

    def test_unmatched_brackets(self):
        for text in ('(', '[', '{', ')', ']', '}', '(()', '[]}', '{text'):
            with self.subTest(text=text):
                self.assertFalse(balanced(text))

    def test_incorrect_order_and_mismatched_types(self):
        for text in (')(', '][', '}{', '([)]', '(]', '{[}]'):
            with self.subTest(text=text):
                self.assertFalse(balanced(text))

    def test_preserves_input_values_and_collection_order(self):
        texts = ['{[()]}', ')(', 'plain text', '[', '']
        original = texts.copy()
        self.assertEqual([balanced(text) for text in texts],
                         [True, False, True, False, True])
        self.assertEqual(texts, original)


if __name__ == '__main__':
    unittest.main()
