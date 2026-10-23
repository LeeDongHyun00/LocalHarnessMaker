import unittest

from solution import balanced, balanced_legacy


class BalancedTests(unittest.TestCase):
    def test_balanced_text(self) -> None:
        for check in (balanced, balanced_legacy):
            for text in ('', 'ordinary text', '()', '[]', '{}', 'a({[b]})c', '()[]{}'):
                with self.subTest(function=check.__name__, text=text):
                    self.assertIs(check(text), True)

    def test_unbalanced_text(self) -> None:
        for check in (balanced, balanced_legacy):
            for text in (')', ']', '}', '(', '[', '{', '([)]', '(]', '())', '(()'):
                with self.subTest(function=check.__name__, text=text):
                    self.assertIs(check(text), False)

    def test_input_collections_are_unchanged(self) -> None:
        for check in (balanced, balanced_legacy):
            for text, expected in (('a([])b', True), ('([)]', False), ('(', False)):
                for collection in (list(text), tuple(text)):
                    with self.subTest(function=check.__name__, collection=collection):
                        original = collection[:]
                        self.assertIs(check(collection), expected)
                        self.assertEqual(collection, original)

    def test_error_behavior(self) -> None:
        for check in (balanced, balanced_legacy):
            for value in (None, 42, ['(', 1]):
                with self.subTest(function=check.__name__, value=value):
                    original = value[:] if isinstance(value, list) else value
                    with self.assertRaises(TypeError):
                        check(value)
                    self.assertEqual(value, original)


if __name__ == '__main__':
    unittest.main()
