import unittest

from solution import balanced


class BalancedTests(unittest.TestCase):
    def test_bracket_nesting(self) -> None:
        cases = {
            '': True,
            'plain text': True,
            'a{b[c(d)e]f}g': True,
            '()[]{}': True,
            ')(': False,
            '([)]': False,
            '(]': False,
            '[': False,
            '}': False,
            '(()': False,
            '())': False,
        }
        for text, expected in cases.items():
            with self.subTest(text=text):
                self.assertIs(balanced(text), expected)


if __name__ == '__main__':
    unittest.main()
