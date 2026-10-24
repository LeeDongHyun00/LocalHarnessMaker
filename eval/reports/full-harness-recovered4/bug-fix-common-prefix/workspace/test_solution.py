import unittest

from solution import common


class CommonTests(unittest.TestCase):
    def test_longest_common_character_prefix(self) -> None:
        cases = [
            ([], ''),
            (['single'], 'single'),
            (['flower', 'flow', 'flight'], 'fl'),
            (['prefix', 'pre'], 'pre'),
            (['same', 'same'], 'same'),
            (['Case', 'case'], ''),
            (['abc', ''], ''),
            (['abc', 'xbc'], ''),
        ]
        for items, expected in cases:
            with self.subTest(items=items):
                original = items.copy()
                self.assertEqual(common(items), expected)
                self.assertEqual(items, original)


if __name__ == '__main__':
    unittest.main()
