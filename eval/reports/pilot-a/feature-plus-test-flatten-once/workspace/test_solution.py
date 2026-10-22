import unittest

from solution import flatten


class FlattenTests(unittest.TestCase):
    def test_preserves_order_and_duplicates(self) -> None:
        self.assertEqual(flatten([[3, 1], [3], [0, -2]]), [3, 1, 3, 0, -2])

    def test_empty_inputs_and_inner_lists(self) -> None:
        for items in ([], [[]], [[], []], [[], [1], [], [2], []]):
            with self.subTest(items=items):
                expected = [1, 2] if any(items) else []
                self.assertEqual(flatten(items), expected)

    def test_single_element(self) -> None:
        self.assertEqual(flatten([[42]]), [42])

    def test_returns_new_list_without_modifying_inputs(self) -> None:
        inner = [1, 2]
        items = [inner, [], inner]
        result = flatten(items)
        self.assertEqual(result, [1, 2, 1, 2])
        self.assertEqual(items, [[1, 2], [], [1, 2]])
        self.assertIs(items[0], inner)
        self.assertIs(items[2], inner)
        self.assertIsNot(result, items)
        self.assertIsNot(result, inner)
        result.append(3)
        self.assertEqual(inner, [1, 2])

    def test_empty_result_is_a_new_list(self) -> None:
        items: list[list[int]] = []
        self.assertIsNot(flatten(items), items)
        self.assertIsNot(flatten(items), flatten(items))


if __name__ == "__main__":
    unittest.main()
