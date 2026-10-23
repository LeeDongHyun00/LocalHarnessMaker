import unittest

from solution import flatten


class FlattenTests(unittest.TestCase):
    def test_preserves_order_and_duplicates(self) -> None:
        self.assertEqual(flatten([[3, -1], [0], [3, 2]]), [3, -1, 0, 3, 2])

    def test_ignores_empty_inner_lists(self) -> None:
        self.assertEqual(flatten([[], [1, 2], [], [3], []]), [1, 2, 3])

    def test_empty_outer_list_returns_new_list(self) -> None:
        items: list[list[int]] = []
        result = flatten(items)
        self.assertEqual(result, [])
        self.assertIsNot(result, items)

    def test_all_empty_inner_lists(self) -> None:
        self.assertEqual(flatten([[], [], []]), [])

    def test_single_item_returns_new_list(self) -> None:
        inner = [42]
        result = flatten([inner])
        self.assertEqual(result, [42])
        self.assertIsNot(result, inner)

    def test_does_not_mutate_input_collections(self) -> None:
        first = [1, 2]
        empty: list[int] = []
        last = [3, 4]
        items = [first, empty, last]
        result = flatten(items)

        self.assertEqual(items, [[1, 2], [], [3, 4]])
        self.assertIs(items[0], first)
        self.assertIs(items[1], empty)
        self.assertIs(items[2], last)
        self.assertIsNot(result, items)
        for inner in items:
            self.assertIsNot(result, inner)

        result.append(5)
        self.assertEqual(items, [[1, 2], [], [3, 4]])

    def test_flattens_exactly_one_level(self) -> None:
        nested = [1, 2]
        items = [[nested], [], [3]]
        result = flatten(items)  # type: ignore[arg-type]
        self.assertEqual(result, [[1, 2], 3])
        self.assertIs(result[0], nested)
        self.assertEqual(items, [[[1, 2]], [], [3]])


if __name__ == "__main__":
    unittest.main()
