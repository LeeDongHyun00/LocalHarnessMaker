import unittest

from solution import balanced


class BalancedTests(unittest.TestCase):
    def test_balanced_text(self) -> None:
        for text in ('', 'plain text', '(a[b]{c})', '()[]{}'):
            with self.subTest(text=text):
                self.assertTrue(balanced(text))

    def test_unbalanced_text(self) -> None:
        for text in (')(', '([)]', '(]', '(', ')', '[', ']', '{', '}'):
            with self.subTest(text=text):
                self.assertFalse(balanced(text))


if __name__ == '__main__':
    unittest.main()
