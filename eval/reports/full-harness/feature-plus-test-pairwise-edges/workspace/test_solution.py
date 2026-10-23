import unittest

from solution import pairs


class PairsTests(unittest.TestCase):
    def test_ordinary_input(self) -> None:
        self.assertEqual(pairs([1, 2, 3]), [(1, 2), (2, 3)])
        self.assertEqual(pairs([-2, 0, 0, 5]), [(-2, 0), (0, 0), (0, 5)])

    def test_two_items(self) -> None:
        self.assertEqual(pairs([4, 9]), [(4, 9)])

    def test_single_item(self) -> None:
        self.assertEqual(pairs([7]), [])

    def test_empty_input(self) -> None:
        self.assertEqual(pairs([]), [])

    def test_input_is_not_mutated(self) -> None:
        for items in ([], [7], [1, 2], [3, 1, 3, 2]):
            with self.subTest(items=items):
                original = items.copy()
                pairs(items)
                self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
