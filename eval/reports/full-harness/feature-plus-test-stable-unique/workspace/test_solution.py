"""Public tests for unique."""

import unittest

from solution import unique


class UniqueTests(unittest.TestCase):
    def test_preserves_first_occurrence_order_and_input(self) -> None:
        items: list[str] = ["pear", "apple", "pear", "banana", "apple"]
        original: list[str] = items.copy()
        result: list[str] = unique(items)
        self.assertEqual(result, ["pear", "apple", "banana"])
        self.assertEqual(items, original)
        self.assertIsNot(result, items)

    def test_equality_is_case_sensitive(self) -> None:
        self.assertEqual(unique(["A", "a", "A", "a"]), ["A", "a"])

    def test_boundary_inputs(self) -> None:
        cases: list[tuple[list[str], list[str]]] = [
            (["only"], ["only"]),
            (["same", "same", "same"], ["same"]),
            (["", "", "value", ""], ["", "value"]),
            (["b", "a", "c"], ["b", "a", "c"]),
        ]
        for items, expected in cases:
            with self.subTest(items=items):
                original: list[str] = items.copy()
                self.assertEqual(unique(items), expected)
                self.assertEqual(items, original)

    def test_empty_input(self) -> None:
        items: list[str] = []
        result: list[str] = unique(items)
        self.assertEqual(result, [])
        self.assertEqual(items, [])
        self.assertIsNot(result, items)


if __name__ == "__main__":
    unittest.main()
