"""Regression tests for the public flatten API."""

import unittest

from solution import flatten


class FlattenTests(unittest.TestCase):
    def test_preserves_all_values_and_order(self):
        self.assertEqual(flatten([[3, 1], [0, -2, 3], [7]]), [3, 1, 0, -2, 3, 7])

    def test_ignores_empty_inner_lists(self):
        self.assertEqual(flatten([[], [1, 2], [], [3], []]), [1, 2, 3])
        self.assertEqual(flatten([[], []]), [])
        self.assertEqual(flatten([]), [])

    def test_returns_new_list_without_mutating_inputs(self):
        first = [1, 2]
        second = [3, 4]
        items = [first, [], second, first]

        result = flatten(items)

        self.assertEqual(result, [1, 2, 3, 4, 1, 2])
        self.assertEqual(items, [[1, 2], [], [3, 4], [1, 2]])
        self.assertIs(items[0], first)
        self.assertIs(items[2], second)
        self.assertIs(items[3], first)
        self.assertIsNot(result, items)
        for group in items:
            self.assertIsNot(result, group)
        result.append(5)
        self.assertEqual(items, [[1, 2], [], [3, 4], [1, 2]])

    def test_flattens_exactly_one_level(self):
        # Runtime behavior also preserves nested values without recursing.
        nested = [1, 2]
        result = flatten([[nested], [], [3]])
        self.assertEqual(result, [[1, 2], 3])
        self.assertIs(result[0], nested)
        self.assertEqual(nested, [1, 2])


if __name__ == "__main__":
    unittest.main()
