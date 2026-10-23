import unittest

from solution import flatten, flatten_legacy


class FlattenTests(unittest.TestCase):
    def test_preserves_order_and_ignores_empty_groups(self):
        for function in (flatten, flatten_legacy):
            with self.subTest(function=function.__name__):
                self.assertEqual(function([[], [3, 1], [], [2, 2], []]), [3, 1, 2, 2])
                self.assertEqual(function([]), [])
                self.assertEqual(function([[], []]), [])

    def test_returns_fresh_list_without_mutating_inputs(self):
        for function in (flatten, flatten_legacy):
            with self.subTest(function=function.__name__):
                first = [1, 2]
                second = [3]
                items = [first, second, first]
                result = function(items)
                self.assertEqual(result, [1, 2, 3, 1, 2])
                self.assertEqual(items, [[1, 2], [3], [1, 2]])
                self.assertIs(items[0], first)
                self.assertIs(items[1], second)
                self.assertIs(items[2], first)
                self.assertIsNot(result, items)
                self.assertIsNot(result, first)
                self.assertIsNot(result, second)
                result.append(4)
                self.assertEqual(items, [[1, 2], [3], [1, 2]])
                self.assertIsNot(function([]), function([]))

    def test_flattens_exactly_one_level(self):
        for function in (flatten, flatten_legacy):
            with self.subTest(function=function.__name__):
                nested = [1, 2]
                items = [[nested], [3]]
                result = function(items)
                self.assertEqual(result, [[1, 2], 3])
                self.assertIs(result[0], nested)
                self.assertEqual(items, [[[1, 2]], [3]])

    def test_preserves_iteration_errors(self):
        for function in (flatten, flatten_legacy):
            for items in (None, 1, [None], [[1], 2]):
                with self.subTest(function=function.__name__, items=items):
                    with self.assertRaises(TypeError):
                        function(items)


if __name__ == "__main__":
    unittest.main()
