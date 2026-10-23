import unittest

from solution import common, common_legacy


class CommonTests(unittest.TestCase):
    def test_common_prefix(self) -> None:
        cases = [
            (['flower', 'flow', 'flight'], 'fl'),
            (['prefix', 'pre', 'prepare'], 'pre'),
            (['same', 'same'], 'same'),
            (['dog', 'racecar', 'car'], ''),
            (['Alpha', 'alpha'], ''),
            (['abc', '', 'abcd'], ''),
            (['éclair', 'école'], 'éc'),
        ]
        for function in (common, common_legacy):
            for items, expected in cases:
                with self.subTest(function=function.__name__, items=items):
                    result = function(items)
                    self.assertEqual(result, expected)
                    self.assertIsInstance(result, str)

    def test_empty_and_single_item(self) -> None:
        for function in (common, common_legacy):
            for items, expected in [([], ''), (['alone'], 'alone'), ([''], '')]:
                with self.subTest(function=function.__name__, items=items):
                    self.assertEqual(function(items), expected)

    def test_input_is_unchanged(self) -> None:
        for function in (common, common_legacy):
            with self.subTest(function=function.__name__):
                items = ['flower', 'flow', 'flight']
                original = items.copy()
                self.assertEqual(function(items), 'fl')
                self.assertEqual(items, original)

    def test_invalid_elements_preserve_errors(self) -> None:
        for function in (common, common_legacy):
            for items, error in [(['x', 1], AttributeError), ([1, 'x'], TypeError)]:
                with self.subTest(function=function.__name__, items=items):
                    original = items.copy()
                    with self.assertRaises(error):
                        function(items)
                    self.assertEqual(items, original)


if __name__ == '__main__':
    unittest.main()
