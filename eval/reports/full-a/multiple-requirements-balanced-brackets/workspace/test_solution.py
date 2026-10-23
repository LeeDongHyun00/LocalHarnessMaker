import unittest

from solution import balanced


class BalancedTests(unittest.TestCase):
    def test_valid_nesting_and_adjacent_pairs(self) -> None:
        for text in ('()', '[]', '{}', '([]{})', '{[()]}', '()[]{}'):
            with self.subTest(text=text):
                self.assertIs(balanced(text), True)

    def test_invalid_order_and_crossed_pairs(self) -> None:
        for text in (')(', '][', '}{', '([)]', '{(})', '(]', '[}'):
            with self.subTest(text=text):
                self.assertIs(balanced(text), False)

    def test_unmatched_brackets(self) -> None:
        for text in ('(', '[', '{', ')', ']', '}', '(()', '[]]', '{[]'):
            with self.subTest(text=text):
                self.assertIs(balanced(text), False)

    def test_empty_text_and_ignored_characters(self) -> None:
        for text in ('', 'plain text', '你好\n123!', 'a(b[c]{d})e', '<>'):
            with self.subTest(text=text):
                self.assertIs(balanced(text), True)
        self.assertIs(balanced('text [ more text'), False)

    def test_input_values_and_collection_order_are_preserved(self) -> None:
        texts = ['z([])', 'a([)]', '', 'z([])', '{word}']
        original = texts.copy()
        self.assertEqual(
            [balanced(text) for text in texts],
            [True, False, True, True, True],
        )
        self.assertEqual(texts, original)


if __name__ == '__main__':
    unittest.main()
