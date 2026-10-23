import unittest

from solution import flatten, flatten_legacy


class FlattenTests(unittest.TestCase):
    def test_preserves_order_and_ignores_empty_groups(self):
        for function in (flatten, flatten_legacy):
            with self.subTest(function=function.__name__):
                self.assertEqual(function([[], [3, 1], [], [2, 2], []]), [3, 1, 2, 2])
                self.assertEqual(function([]), [])
                self.assertEqual(function([[], []]), [])

    def test_returns_new_list_without_mutating_inputs(self):
        for function in (flatten, flatten_legacy):
            with self.subTest(function=function.__name__):
                first = [1, 2]
                second = [3]
                items = [first, second]
                result = function(items)
                self.assertIs(type(result), list)
                self.assertIsNot(result, items)
                self.assertIsNot(result, first)
                self.assertIsNot(result, second)
                self.assertEqual(items, [[1, 2], [3]])
                self.assertIs(items[0], first)
                self.assertIs(items[1], second)
                result.append(4)
                self.assertEqual(items, [[1, 2], [3]])

    def test_flattens_exactly_one_level(self):
        for function in (flatten, flatten_legacy):
            with self.subTest(function=function.__name__):
                nested = [1, 2]
                self.assertEqual(function([[nested], [3]]), [nested, 3])
                self.assertIs(function([[nested]])[0], nested)

    def test_invalid_inputs_keep_type_errors(self):
        for function in (flatten, flatten_legacy):
            for items in (None, [None], [1]):
                with self.subTest(function=function.__name__, items=items):
                    with self.assertRaises(TypeError):
                        function(items)


if __name__ == "__main__":
    unittest.main()
