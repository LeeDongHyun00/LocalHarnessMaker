import unittest

from solution import runs


class RunsTests(unittest.TestCase):
    def test_empty_input(self) -> None:
        self.assertEqual(runs([]), [])

    def test_single_value(self) -> None:
        self.assertEqual(runs(["hello"]), [("hello", 1)])

    def test_adjacent_equal_values_are_counted(self) -> None:
        self.assertEqual(
            runs(["a", "a", "b", "b", "b", "c", "c"]),
            [("a", 2), ("b", 3), ("c", 2)],
        )

    def test_nonadjacent_equal_values_form_separate_runs(self) -> None:
        self.assertEqual(
            runs(["a", "a", "b", "a", "a", "a", "b"]),
            [("a", 2), ("b", 1), ("a", 3), ("b", 1)],
        )

    def test_distinct_values_keep_input_order(self) -> None:
        self.assertEqual(
            runs(["z", "a", "m"]),
            [("z", 1), ("a", 1), ("m", 1)],
        )

    def test_string_values_are_preserved_exactly(self) -> None:
        self.assertEqual(
            runs([" A ", " A ", "a", "", "", "\u00e9", "e\u0301", "\u00e9"]),
            [(" A ", 2), ("a", 1), ("", 2), ("\u00e9", 1), ("e\u0301", 1), ("\u00e9", 1)],
        )

    def test_input_collection_is_not_mutated(self) -> None:
        items = ["z", "z", "a", "z"]
        original = items.copy()

        self.assertEqual(runs(items), [("z", 2), ("a", 1), ("z", 1)])
        self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
