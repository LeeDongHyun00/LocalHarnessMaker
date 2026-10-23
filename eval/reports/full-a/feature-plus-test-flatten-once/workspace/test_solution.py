"""Tests for the public flatten API."""

import unittest

from solution import flatten


class FlattenTests(unittest.TestCase):
    def test_ordinary_lists_preserve_order(self) -> None:
        self.assertEqual(flatten([[3, 1], [2, 2], [-1, 0]]), [3, 1, 2, 2, -1, 0])

    def test_empty_inputs_and_inner_lists(self) -> None:
        for items in ([], [[]], [[], [], []], [[], [1], [], [2], []]):
            with self.subTest(items=items):
                expected = [1, 2] if items == [[], [1], [], [2], []] else []
                self.assertEqual(flatten(items), expected)

    def test_single_element_returns_new_list(self) -> None:
        inner = [7]
        items = [inner]
        result = flatten(items)
        self.assertEqual(result, [7])
        self.assertIsNot(result, inner)
        self.assertIsNot(result, items)
        result.append(8)
        self.assertEqual(items, [[7]])
        self.assertIs(items[0], inner)

    def test_shared_inner_list_is_not_modified(self) -> None:
        inner = [1, 2]
        items = [inner, [], inner]
        self.assertEqual(flatten(items), [1, 2, 1, 2])
        self.assertEqual(items, [[1, 2], [], [1, 2]])
        self.assertIs(items[0], inner)
        self.assertIs(items[2], inner)


if __name__ == "__main__":
    unittest.main()
