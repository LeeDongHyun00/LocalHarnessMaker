import unittest

from solution import runs


class RunsTests(unittest.TestCase):
    def test_empty_input(self) -> None:
        self.assertEqual(runs([]), [])

    def test_adjacent_equal_strings_are_counted(self) -> None:
        self.assertEqual(runs(["a", "a", "a", "b", "b"]), [("a", 3), ("b", 2)])

    def test_nonadjacent_equal_strings_form_separate_runs(self) -> None:
        self.assertEqual(
            runs(["b", "b", "a", "b", "b", "b", "a"]),
            [("b", 2), ("a", 1), ("b", 3), ("a", 1)],
        )

    def test_values_and_input_order_are_preserved(self) -> None:
        items = [" z ", " z ", "", "A", "a", "é", "e\u0301", " z "]
        original = items.copy()
        self.assertEqual(
            runs(items),
            [(" z ", 2), ("", 1), ("A", 1), ("a", 1), ("é", 1), ("e\u0301", 1), (" z ", 1)],
        )
        self.assertEqual(items, original)

    def test_single_value(self) -> None:
        self.assertEqual(runs(["only"]), [("only", 1)])


if __name__ == "__main__":
    unittest.main()
