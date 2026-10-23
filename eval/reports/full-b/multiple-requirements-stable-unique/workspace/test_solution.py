import unittest

from solution import unique


class UniqueTests(unittest.TestCase):
    def test_empty_input(self) -> None:
        self.assertEqual(unique([]), [])

    def test_duplicates_keep_first_occurrence_order(self) -> None:
        self.assertEqual(
            unique(["pear", "apple", "pear", "banana", "apple", "banana"]),
            ["pear", "apple", "banana"],
        )

    def test_distinct_strings_keep_input_order(self) -> None:
        self.assertEqual(unique(["z", "b", "a"]), ["z", "b", "a"])

    def test_equality_is_case_sensitive(self) -> None:
        self.assertEqual(
            unique(["Apple", "apple", "APPLE", "Apple", "apple"]),
            ["Apple", "apple", "APPLE"],
        )

    def test_string_values_are_preserved(self) -> None:
        self.assertEqual(
            unique(["", " ", " a ", "a", "\t", "é", "e\u0301", "", " a "]),
            ["", " ", " a ", "a", "\t", "é", "e\u0301"],
        )

    def test_input_values_and_order_are_unchanged(self) -> None:
        items = ["pear", "apple", "pear", "", "Apple", "apple"]
        original = items.copy()

        self.assertEqual(unique(items), ["pear", "apple", "", "Apple"])
        self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
