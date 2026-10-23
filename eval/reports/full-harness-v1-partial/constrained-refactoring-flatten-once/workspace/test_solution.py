import unittest

from solution import flatten, flatten_legacy


class FlattenTests(unittest.TestCase):
    def test_order_and_empty_groups(self):
        for function in (flatten, flatten_legacy):
            for items, expected in (
                ([], []),
                ([[], []], []),
                ([[3, 1], [], [2, 3], []], [3, 1, 2, 3]),
            ):
                with self.subTest(function=function.__name__, items=items):
                    self.assertEqual(function(items), expected)

    def test_new_result_and_input_immutability(self):
        for function in (flatten, flatten_legacy):
            with self.subTest(function=function.__name__):
                first = [1, 2]
                second = [3]
                items = [first, [], second]
                result = function(items)
                self.assertIsNot(result, items)
                self.assertIsNot(result, first)
                self.assertIsNot(result, second)
                result.append(4)
                self.assertEqual(items, [[1, 2], [], [3]])
                self.assertIs(items[0], first)
                self.assertIs(items[2], second)
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

    def test_invalid_inputs_preserve_type_errors(self):
        for function in (flatten, flatten_legacy):
            for items in (None, 1, [None], [[1], 2]):
                with self.subTest(function=function.__name__, items=items):
                    with self.assertRaises(TypeError):
                        function(items)


if __name__ == "__main__":
    unittest.main()
