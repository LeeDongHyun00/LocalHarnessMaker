import unittest

from solution import flatten


class FlattenTests(unittest.TestCase):
    def test_ordinary_input_preserves_order(self):
        self.assertEqual(flatten([[3, 1], [2, 2], [-1, 0]]), [3, 1, 2, 2, -1, 0])

    def test_empty_inputs(self):
        for items in ([], [[]], [[], [], []]):
            with self.subTest(items=items):
                result = flatten(items)
                self.assertEqual(result, [])
                self.assertIsNot(result, items)

    def test_single_element_and_empty_inner_lists(self):
        self.assertEqual(flatten([[7]]), [7])
        self.assertEqual(flatten([[], [0], [], [-5], []]), [0, -5])

    def test_returns_new_list_without_mutating_inputs(self):
        first = [1, 2]
        second = [3]
        items = [first, [], second]
        result = flatten(items)
        self.assertEqual(items, [[1, 2], [], [3]])
        self.assertIs(items[0], first)
        self.assertIs(items[2], second)
        self.assertIsNot(result, items)
        self.assertIsNot(result, first)
        self.assertEqual(result, [1, 2, 3])
        result.append(4)
        self.assertEqual(items, [[1, 2], [], [3]])

    def test_flattens_exactly_one_level(self):
        nested = [1, 2]
        result = flatten([[nested], [], [3]])
        self.assertEqual(result, [[1, 2], 3])
        self.assertIs(result[0], nested)
        self.assertEqual(nested, [1, 2])


if __name__ == "__main__":
    unittest.main()
