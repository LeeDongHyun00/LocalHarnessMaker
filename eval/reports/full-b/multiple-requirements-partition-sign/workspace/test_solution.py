import unittest

from solution import partition


class PartitionTests(unittest.TestCase):
    def test_mixed_values_preserve_order_and_duplicates(self) -> None:
        items = [4, -2, 0, -5, 4, -2, 0, 1, -1]

        self.assertEqual(
            partition(items),
            ([-2, -5, -2, -1], [0, 0], [4, 4, 1]),
        )

    def test_empty_input_returns_three_lists(self) -> None:
        self.assertEqual(partition([]), ([], [], []))

    def test_single_partition_inputs(self) -> None:
        cases = [
            ([-1, -4, -1], ([-1, -4, -1], [], [])),
            ([0, 0, 0], ([], [0, 0, 0], [])),
            ([5, 2, 5], ([], [], [5, 2, 5])),
        ]
        for items, expected in cases:
            with self.subTest(items=items):
                self.assertEqual(partition(items), expected)

    def test_input_is_not_mutated(self) -> None:
        items = [9, -2, 0, 3, -7, 0, 9]
        original = items.copy()

        result = partition(items)

        self.assertEqual(items, original)
        for group in result:
            group.append(42)
        self.assertEqual(items, original)

    def test_large_integer_values_are_preserved(self) -> None:
        large = 10**100
        items = [large + 1, -large, 0, large, -large - 1]

        self.assertEqual(
            partition(items),
            ([-large, -large - 1], [0], [large + 1, large]),
        )


if __name__ == "__main__":
    unittest.main()
