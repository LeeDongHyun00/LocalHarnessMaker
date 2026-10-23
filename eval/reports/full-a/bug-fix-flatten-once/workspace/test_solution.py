import unittest

from solution import flatten


class FlattenTests(unittest.TestCase):
    def test_flattens_all_items_in_order_without_mutating_inputs(self) -> None:
        items = [[1, 2], [], [3, 4, 5]]
        result = flatten(items)

        self.assertEqual(result, [1, 2, 3, 4, 5])
        self.assertEqual(items, [[1, 2], [], [3, 4, 5]])
        self.assertIsNot(result, items)
        for group in items:
            self.assertIsNot(result, group)

    def test_empty_inputs_return_a_new_empty_list(self) -> None:
        items: list[list[int]] = []
        result = flatten(items)

        self.assertEqual(result, [])
        self.assertIsNot(result, items)
        self.assertEqual(flatten([[], []]), [])


if __name__ == "__main__":
    unittest.main()
