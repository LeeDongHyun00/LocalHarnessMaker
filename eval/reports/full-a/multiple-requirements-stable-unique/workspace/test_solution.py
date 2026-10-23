import unittest

from solution import unique


class UniqueTests(unittest.TestCase):
    def test_preserves_first_occurrence_order(self) -> None:
        self.assertEqual(
            unique(["pear", "apple", "pear", "banana", "apple"]),
            ["pear", "apple", "banana"],
        )

    def test_empty_input(self) -> None:
        self.assertEqual(unique([]), [])

    def test_equality_is_case_sensitive(self) -> None:
        self.assertEqual(unique(["A", "a", "A", "a"]), ["A", "a"])

    def test_preserves_string_values(self) -> None:
        self.assertEqual(
            unique(["", " a ", "a", "", "é", "e\u0301", " a "]),
            ["", " a ", "a", "é", "e\u0301"],
        )

    def test_does_not_mutate_or_alias_input(self) -> None:
        items = ["z", "a", "z", "B"]
        original = items.copy()
        result = unique(items)
        self.assertEqual(items, original)
        self.assertIsNot(result, items)
        result.append("new")
        self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
