"""Tests for the public unique API."""

import unittest

from solution import unique


class UniqueTests(unittest.TestCase):
    def test_duplicates_preserve_first_occurrence_order(self) -> None:
        self.assertEqual(
            unique(["pear", "apple", "pear", "banana", "apple", "banana"]),
            ["pear", "apple", "banana"],
        )

    def test_distinct_strings_preserve_order(self) -> None:
        self.assertEqual(unique(["c", "a", "b"]), ["c", "a", "b"])

    def test_equality_is_case_sensitive(self) -> None:
        self.assertEqual(
            unique(["Apple", "apple", "APPLE", "Apple", "apple"]),
            ["Apple", "apple", "APPLE"],
        )

    def test_boundary_inputs(self) -> None:
        cases: list[tuple[list[str], list[str]]] = [
            (["only"], ["only"]),
            (["same", "same", "same"], ["same"]),
            (["", "", " ", ""], ["", " "]),
        ]
        for items, expected in cases:
            with self.subTest(items=items):
                self.assertEqual(unique(items), expected)

    def test_empty_input(self) -> None:
        self.assertEqual(unique([]), [])

    def test_input_is_not_mutated(self) -> None:
        items = ["b", "a", "b", "c", "a"]
        original = items.copy()
        self.assertEqual(unique(items), ["b", "a", "c"])
        self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
