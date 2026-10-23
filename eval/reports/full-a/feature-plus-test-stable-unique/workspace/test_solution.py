"""Tests for the public unique API."""

import unittest

from solution import unique


class UniqueTests(unittest.TestCase):
    def test_duplicates_preserve_first_occurrence_order(self) -> None:
        items = ["pear", "apple", "pear", "banana", "apple"]
        original = items.copy()
        self.assertEqual(unique(items), ["pear", "apple", "banana"])
        self.assertEqual(items, original)

    def test_empty_input(self) -> None:
        self.assertEqual(unique([]), [])

    def test_single_string_and_repeated_string(self) -> None:
        self.assertEqual(unique(["only"]), ["only"])
        self.assertEqual(unique(["same", "same", "same"]), ["same"])

    def test_case_sensitive_and_empty_strings(self) -> None:
        self.assertEqual(
            unique(["", "A", "a", "", "A", " "]),
            ["", "A", "a", " "],
        )

    def test_distinct_strings_keep_their_order(self) -> None:
        self.assertEqual(unique(["z", "b", "a"]), ["z", "b", "a"])


if __name__ == "__main__":
    unittest.main()
