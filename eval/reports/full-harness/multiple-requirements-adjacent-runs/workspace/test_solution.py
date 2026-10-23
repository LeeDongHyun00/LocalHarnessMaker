import unittest

from solution import runs


class RunsTests(unittest.TestCase):
    def test_empty_input(self) -> None:
        self.assertEqual(runs([]), [])

    def test_adjacent_equal_values(self) -> None:
        self.assertEqual(runs(["a", "a", "a", "b", "b"]), [("a", 3), ("b", 2)])

    def test_nonadjacent_equal_values_remain_separate(self) -> None:
        self.assertEqual(
            runs(["b", "b", "a", "b", "b", "b"]),
            [("b", 2), ("a", 1), ("b", 3)],
        )

    def test_values_and_input_order_are_preserved(self) -> None:
        items = ["", "", " A ", "a", "한글", "한글", ""]
        original = items.copy()
        self.assertEqual(
            runs(items), [("", 2), (" A ", 1), ("a", 1), ("한글", 2), ("", 1)]
        )
        self.assertEqual(items, original)

    def test_single_value(self) -> None:
        self.assertEqual(runs(["only"]), [("only", 1)])


if __name__ == "__main__":
    unittest.main()
