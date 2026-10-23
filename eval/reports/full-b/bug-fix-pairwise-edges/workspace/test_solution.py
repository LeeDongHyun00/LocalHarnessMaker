import unittest

from solution import pairs


class PairsTests(unittest.TestCase):
    def test_overlapping_adjacent_pairs(self) -> None:
        items = [1, 2, 3, 4]

        self.assertEqual(pairs(items), [(1, 2), (2, 3), (3, 4)])
        self.assertEqual(items, [1, 2, 3, 4])

    def test_fewer_than_two_items(self) -> None:
        for items in ([], [1]):
            with self.subTest(items=items):
                self.assertEqual(pairs(items), [])


if __name__ == "__main__":
    unittest.main()
