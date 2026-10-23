import unittest

from solution import flatten


class FlattenTests(unittest.TestCase):
    def test_preserves_all_items_and_leaves_input_unchanged(self) -> None:
        items = [[], [1, 2], [], [3, 4, 5], []]
        original = [group.copy() for group in items]

        result = flatten(items)

        self.assertEqual(result, [1, 2, 3, 4, 5])
        self.assertEqual(items, original)
        self.assertIsNot(result, items)
        for group in items:
            self.assertIsNot(result, group)

    def test_empty_input_returns_a_new_list(self) -> None:
        items: list[list[int]] = []

        result = flatten(items)

        self.assertEqual(result, [])
        self.assertIsNot(result, items)


if __name__ == "__main__":
    unittest.main()
