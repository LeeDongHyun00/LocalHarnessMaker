import unittest

from solution import common, common_legacy


class CommonTests(unittest.TestCase):
    def test_prefix_cases(self) -> None:
        cases = [
            ([], ''),
            (['single'], 'single'),
            (['flower', 'flow', 'flight'], 'fl'),
            (['same', 'same'], 'same'),
            (['abc', 'abcdef'], 'abc'),
            (['abc', ''], ''),
            (['dog', 'cat'], ''),
            (['Prefix', 'prefix'], ''),
            (['한글', '한국'], '한'),
        ]
        for function in (common, common_legacy):
            for items, expected in cases:
                with self.subTest(function=function.__name__, items=items):
                    result = function(items)
                    self.assertEqual(result, expected)
                    self.assertIsInstance(result, str)

    def test_input_is_unchanged(self) -> None:
        for function in (common, common_legacy):
            with self.subTest(function=function.__name__):
                items = ['flower', 'flow', 'flight']
                original = items.copy()
                self.assertEqual(function(items), 'fl')
                self.assertEqual(items, original)

    def test_existing_error_behavior(self) -> None:
        for function in (common, common_legacy):
            for items, error in [
                (['abc', None], AttributeError),
                ([1, 'abc'], TypeError),
            ]:
                with self.subTest(function=function.__name__, items=items):
                    original = items.copy()
                    with self.assertRaises(error):
                        function(items)
                    self.assertEqual(items, original)


if __name__ == '__main__':
    unittest.main()
