import unittest

from solution import pairs


class PairsTests(unittest.TestCase):
    def test_adjacent_pairs_preserve_order_and_input(self) -> None:
        for items in ([], [1], [1, 2], [1, 2, 3], [3, 1, 3, 2]):
            with self.subTest(items=items):
                original = items.copy()
                expected = [(items[i], items[i + 1]) for i in range(len(items) - 1)]
                self.assertEqual(pairs(items), expected)
                self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
