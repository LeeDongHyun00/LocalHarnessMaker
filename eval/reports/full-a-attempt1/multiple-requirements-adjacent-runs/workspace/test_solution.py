import unittest

from solution import runs


class RunsTests(unittest.TestCase):
    def test_empty_input(self) -> None:
        self.assertEqual(runs([]), [])

    def test_adjacent_equal_values_are_counted(self) -> None:
        self.assertEqual(runs(["a", "a", "b", "b", "b"]),
                         [("a", 2), ("b", 3)])

    def test_nonadjacent_equal_values_form_separate_runs(self) -> None:
        self.assertEqual(runs(["b", "a", "b", "b", "a"]),
                         [("b", 1), ("a", 1), ("b", 2), ("a", 1)])

    def test_values_and_input_order_are_preserved(self) -> None:
        items = ["", "", " A ", "a", "\u00e9", "e\u0301", "\n", ""]
        original = items.copy()
        self.assertEqual(runs(items),
                         [("", 2), (" A ", 1), ("a", 1), ("\u00e9", 1),
                          ("e\u0301", 1), ("\n", 1), ("", 1)])
        self.assertEqual(items, original)

    def test_single_value(self) -> None:
        self.assertEqual(runs(["only"]), [("only", 1)])


if __name__ == "__main__":
    unittest.main()
