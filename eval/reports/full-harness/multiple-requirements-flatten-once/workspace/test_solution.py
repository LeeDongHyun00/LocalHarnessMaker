import unittest

from solution import flatten


class FlattenTests(unittest.TestCase):
    def test_preserves_all_values_and_order(self):
        self.assertEqual(flatten([[3, 1, 3], [0, -2], [4]]), [3, 1, 3, 0, -2, 4])

    def test_ignores_empty_inner_lists(self):
        self.assertEqual(flatten([[], [2, 1], [], [3], []]), [2, 1, 3])
        self.assertEqual(flatten([[], []]), [])
        self.assertEqual(flatten([]), [])

    def test_returns_new_list_without_mutating_inputs(self):
        first = [2, 1]
        empty = []
        items = [first, empty, first]

        result = flatten(items)

        self.assertEqual(result, [2, 1, 2, 1])
        self.assertEqual(items, [[2, 1], [], [2, 1]])
        self.assertIs(items[0], first)
        self.assertIs(items[1], empty)
        self.assertIs(items[2], first)
        self.assertIsNot(result, items)
        self.assertIsNot(result, first)
        result.append(9)
        self.assertEqual(first, [2, 1])
        self.assertEqual(empty, [])

    def test_flattens_exactly_one_level(self):
        nested = [1, 2]
        items = [[nested], [], [3]]

        result = flatten(items)

        self.assertEqual(result, [[1, 2], 3])
        self.assertIs(result[0], nested)
        self.assertEqual(items, [[[1, 2]], [], [3]])


if __name__ == "__main__":
    unittest.main()
