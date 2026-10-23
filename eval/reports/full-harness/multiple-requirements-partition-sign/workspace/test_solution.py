from unittest import TestCase, main

from solution import partition


class PartitionTests(TestCase):
    def test_preserves_order_and_duplicates(self: TestCase) -> None:
        items = [3, -2, 0, -5, 1, -2, 0, 3]
        self.assertEqual(partition(items), ([-2, -5, -2], [0, 0], [3, 1, 3]))

    def test_empty_input(self: TestCase) -> None:
        result = partition([])
        self.assertEqual(result, ([], [], []))
        self.assertIsInstance(result, tuple)
        for group in result:
            self.assertIsInstance(group, list)
        self.assertEqual(len({id(group) for group in result}), 3)

    def test_single_partition_inputs(self: TestCase) -> None:
        for items, expected in [
            ([-1, -3, -1], ([-1, -3, -1], [], [])),
            ([0, 0, 0], ([], [0, 0, 0], [])),
            ([4, 2, 4], ([], [], [4, 2, 4])),
        ]:
            with self.subTest(items=items):
                self.assertEqual(partition(items), expected)

    def test_preserves_input_and_returns_independent_lists(self: TestCase) -> None:
        items = [2, 0, -3, 2, -1]
        original = items.copy()
        result = partition(items)
        self.assertEqual(items, original)
        for group in result:
            self.assertIsNot(group, items)
            group.append(99)
        self.assertEqual(items, original)
        self.assertEqual(partition(items), ([-3, -1], [0], [2, 2]))


if __name__ == "__main__":
    main()
