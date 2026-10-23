import unittest

from solution import flatten, flatten_legacy


class FlattenTests(unittest.TestCase):
    def test_preserves_order_and_ignores_empty_groups(self):
        for function in (flatten, flatten_legacy):
            with self.subTest(function=function.__name__):
                self.assertEqual(function([[], [3, 1], [], [2, 3], []]), [3, 1, 2, 3])
                self.assertEqual(function([]), [])
                self.assertEqual(function([[], []]), [])

    def test_returns_fresh_list_without_mutating_input(self):
        for function in (flatten, flatten_legacy):
            with self.subTest(function=function.__name__):
                group = [1, 2]
                items = [group, [], group]
                result = function(items)
                self.assertEqual(result, [1, 2, 1, 2])
                self.assertIsNot(result, items)
                self.assertIsNot(result, group)
                self.assertIsNot(result, function(items))
                result.append(3)
                self.assertEqual(items, [[1, 2], [], [1, 2]])
                self.assertIs(items[0], group)
                self.assertIs(items[2], group)

    def test_flattens_exactly_one_level(self):
        for function in (flatten, flatten_legacy):
            with self.subTest(function=function.__name__):
                nested = [1, 2]
                items = [[nested], []]
                result = function(items)
                self.assertEqual(result, [[1, 2]])
                self.assertIs(result[0], nested)
                self.assertEqual(items, [[[1, 2]], []])

    def test_preserves_type_errors_for_noniterable_inputs(self):
        for function in (flatten, flatten_legacy):
            for items in (None, 1, [None], [[1], 2]):
                with self.subTest(function=function.__name__, items=items):
                    with self.assertRaises(TypeError):
                        function(items)


if __name__ == "__main__":
    unittest.main()
