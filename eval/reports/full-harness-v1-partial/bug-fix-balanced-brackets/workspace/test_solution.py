import unittest

from solution import balanced


class BalancedTests(unittest.TestCase):
    def test_bracket_nesting(self) -> None:
        for text in ('', 'plain text', 'a({b[c]})d', '()[]{}'):
            with self.subTest(text=text):
                self.assertTrue(balanced(text))

        for text in (')(', '([)]', '(]', '(', ')', '[', ']', '{', '}'):
            with self.subTest(text=text):
                self.assertFalse(balanced(text))

    def test_ignored_characters_and_unmatched_suffixes(self) -> None:
        text = 'prefix {a[1 + (2)]}\n suffix'
        self.assertTrue(balanced(text))
        self.assertEqual(text, 'prefix {a[1 + (2)]}\n suffix')
        for suffix in ('(', '[', '{', ')', ']', '}'):
            with self.subTest(suffix=suffix):
                self.assertFalse(balanced(text + suffix))


if __name__ == '__main__':
    unittest.main()
