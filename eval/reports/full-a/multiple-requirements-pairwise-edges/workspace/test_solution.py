import unittest

from solution import pairs


class PairsTests(unittest.TestCase):
    def test_overlapping_pairs(self):
        self.assertEqual(pairs([1, 2, 3]), [(1, 2), (2, 3)])
        self.assertEqual(pairs([1, 2, 3, 4]), [(1, 2), (2, 3), (3, 4)])

    def test_short_inputs(self):
        self.assertEqual(pairs([]), [])
        self.assertEqual(pairs([7]), [])
        self.assertEqual(pairs([7, 8]), [(7, 8)])

    def test_preserves_values_order_and_input(self):
        items = [5, -2, 5, 0, -10]
        original = items.copy()
        self.assertEqual(pairs(items), [(5, -2), (-2, 5), (5, 0), (0, -10)])
        self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
