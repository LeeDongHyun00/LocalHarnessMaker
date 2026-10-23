import unittest

from solution import balanced, balanced_legacy


class BalancedTests(unittest.TestCase):
    def test_empty_and_balanced_text(self) -> None:
        for check in (balanced, balanced_legacy):
            for text in ('', '()', '[]', '{}', '()[]{}', '{[()]}'):
                with self.subTest(function=check.__name__, text=text):
                    self.assertIs(check(text), True)

    def test_unmatched_and_mismatched_brackets(self) -> None:
        for check in (balanced, balanced_legacy):
            for text in (')', ']', '}', '(', '[', '{', '([)]', '(]', '(()', '())', '[]('):
                with self.subTest(function=check.__name__, text=text):
                    self.assertIs(check(text), False)

    def test_other_characters_are_ignored(self) -> None:
        for check in (balanced, balanced_legacy):
            for text, expected in (
                ('plain text\n汉字🙂', True),
                ('before [a + (b * {c})] after', True),
                ('before [a + (b] after', False),
            ):
                with self.subTest(function=check.__name__, text=text):
                    self.assertIs(check(text), expected)

    def test_input_collections_are_unchanged(self) -> None:
        for check in (balanced, balanced_legacy):
            for collection in (list, tuple):
                for text, expected in (('', True), ('{[a]}', True), ('([)]', False), (')(', False), ('[', False)):
                    characters = collection(text)
                    original = characters[:]
                    with self.subTest(function=check.__name__, collection=collection.__name__, text=text):
                        self.assertIs(check(characters), expected)
                        self.assertEqual(characters, original)

    def test_invalid_input_types_raise_type_error(self) -> None:
        for check in (balanced, balanced_legacy):
            for text in (None, 42, True, ['(', 1, ')']):
                with self.subTest(function=check.__name__, text=text):
                    with self.assertRaises(TypeError):
                        check(text)


if __name__ == '__main__':
    unittest.main()
