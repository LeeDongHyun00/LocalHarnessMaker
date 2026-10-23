import unittest

from solution import pairs


class PairsTests(unittest.TestCase):
    def test_overlapping_adjacent_pairs(self) -> None:
        self.assertEqual(pairs([1, 2, 3]), [(1, 2), (2, 3)])
        self.assertEqual(
            pairs([1, 2, 3, 4]), [(1, 2), (2, 3), (3, 4)]
        )

    def test_fewer_than_two_items(self) -> None:
        for items in ([], [7]):
            with self.subTest(items=items):
                self.assertEqual(pairs(items), [])

    def test_exactly_two_items(self) -> None:
        self.assertEqual(pairs([8, 3]), [(8, 3)])

    def test_preserves_values_duplicates_and_order(self) -> None:
        self.assertEqual(
            pairs([9, -2, 9, 0, 10**100]),
            [(9, -2), (-2, 9), (9, 0), (0, 10**100)],
        )

    def test_does_not_mutate_input(self) -> None:
        for items in ([], [7], [3, 1, 4, 1, 5]):
            with self.subTest(items=items):
                original = items.copy()
                pairs(items)
                self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
