import unittest

from solution import unique


class UniqueTests(unittest.TestCase):
    def test_duplicates_preserve_first_occurrence_order(self) -> None:
        self.assertEqual(
            unique(["pear", "apple", "pear", "banana", "apple"]),
            ["pear", "apple", "banana"],
        )

    def test_empty_input(self) -> None:
        self.assertEqual(unique([]), [])

    def test_equality_is_case_sensitive(self) -> None:
        self.assertEqual(
            unique(["Apple", "apple", "APPLE", "Apple", "apple"]),
            ["Apple", "apple", "APPLE"],
        )

    def test_preserves_values_and_does_not_mutate_input(self) -> None:
        items = [" z ", "", "a", " z ", "", "Z"]
        original = items.copy()

        result = unique(items)

        self.assertEqual(result, [" z ", "", "a", "Z"])
        self.assertEqual(items, original)
        self.assertIsNot(result, items)
        result.append("new")
        self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
