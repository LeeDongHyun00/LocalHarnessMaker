import unittest

from solution import flatten


class FlattenTests(unittest.TestCase):
    def test_flattens_all_items_in_order_without_mutating_input(self) -> None:
        items = [[1, 2], [], [3, 4], [5]]
        original = [group.copy() for group in items]

        result = flatten(items)

        self.assertEqual(result, [1, 2, 3, 4, 5])
        self.assertEqual(items, original)
        self.assertIsNot(result, items)
        for group in items:
            self.assertIsNot(result, group)


if __name__ == "__main__":
    unittest.main()
