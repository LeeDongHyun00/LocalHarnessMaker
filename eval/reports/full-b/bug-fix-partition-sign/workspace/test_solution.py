import unittest

from solution import partition


class PartitionTests(unittest.TestCase):
    def test_preserves_order_duplicates_zeros_and_input(self) -> None:
        items = [4, -1, 0, 2, -3, 0, -1, 4]
        original = items.copy()

        self.assertEqual(partition(items), ([-1, -3, -1], [0, 0], [4, 2, 4]))
        self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
