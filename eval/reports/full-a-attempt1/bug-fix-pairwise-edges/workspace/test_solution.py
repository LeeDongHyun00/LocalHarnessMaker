import unittest

from solution import pairs


class PairsTests(unittest.TestCase):
    def test_overlapping_pairs_preserve_order_and_input(self) -> None:
        items = [1, 2, 3, 4]
        self.assertEqual(pairs(items), [(1, 2), (2, 3), (3, 4)])
        self.assertEqual(items, [1, 2, 3, 4])

    def test_short_inputs(self) -> None:
        for items in ([], [1]):
            with self.subTest(items=items):
                self.assertEqual(pairs(items), [])


if __name__ == "__main__":
    unittest.main()
