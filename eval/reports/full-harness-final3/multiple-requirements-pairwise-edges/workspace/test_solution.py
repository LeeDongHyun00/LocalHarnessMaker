import unittest

from solution import pairs


class PairsTests(unittest.TestCase):
    def test_overlapping_adjacent_pairs_in_input_order(self) -> None:
        self.assertEqual(pairs([1, 2, 3]), [(1, 2), (2, 3)])
        self.assertEqual(pairs([4, 1, 3, 2]), [(4, 1), (1, 3), (3, 2)])

    def test_fewer_than_two_items(self) -> None:
        for items in ([], [7]):
            with self.subTest(items=items):
                self.assertEqual(pairs(items), [])

    def test_two_items(self) -> None:
        self.assertEqual(pairs([9, -2]), [(9, -2)])

    def test_preserves_values_and_input_order_without_mutation(self) -> None:
        items = [3, -1, 3, 0, -1]
        original = items.copy()

        result = pairs(items)

        self.assertEqual(result, [(3, -1), (-1, 3), (3, 0), (0, -1)])
        self.assertEqual(items, original)
        self.assertEqual(pairs(items), result)


if __name__ == "__main__":
    unittest.main()
