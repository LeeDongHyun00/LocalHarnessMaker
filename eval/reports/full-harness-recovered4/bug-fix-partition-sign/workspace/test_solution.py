import unittest

from solution import partition


class PartitionTests(unittest.TestCase):
    def test_preserves_order_duplicates_zeros_and_input(self) -> None:
        items = [3, -1, 0, -4, 2, 0, -1, 3]
        original = items.copy()

        self.assertEqual(partition(items), ([-1, -4, -1], [0, 0], [3, 2, 3]))
        self.assertEqual(items, original)

    def test_empty_input(self) -> None:
        self.assertEqual(partition([]), ([], [], []))


if __name__ == "__main__":
    unittest.main()
