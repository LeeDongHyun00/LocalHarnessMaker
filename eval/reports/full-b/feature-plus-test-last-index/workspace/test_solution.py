"""Tests for the public last_index API."""

import unittest

from solution import last_index


class LastIndexTests(unittest.TestCase):
    def test_returns_last_matching_index(self) -> None:
        self.assertEqual(last_index(["red", "blue", "red", "green"], "red"), 2)
        self.assertEqual(last_index(["red", "red", "red"], "red"), 2)

    def test_boundary_matches(self) -> None:
        cases = [
            (["red", "blue", "green"], "red", 0),
            (["red", "blue", "green"], "green", 2),
            (["red"], "red", 0),
        ]
        for items, target, expected in cases:
            with self.subTest(items=items, target=target):
                self.assertEqual(last_index(items, target), expected)

    def test_absent_target_returns_none(self) -> None:
        self.assertIsNone(last_index(["red", "blue"], "green"))
        self.assertIsNone(last_index(["red"], "blue"))

    def test_empty_input_returns_none(self) -> None:
        self.assertIsNone(last_index([], "red"))
        self.assertIsNone(last_index([], ""))

    def test_matching_is_case_sensitive(self) -> None:
        items = ["red", "Red", "red"]
        self.assertEqual(last_index(items, "Red"), 1)
        self.assertEqual(last_index(items, "red"), 2)
        self.assertIsNone(last_index(items, "RED"))

    def test_empty_string_matches(self) -> None:
        self.assertEqual(last_index(["", "red", "", "blue"], ""), 2)

    def test_input_is_not_mutated(self) -> None:
        items = ["red", "blue", "red", "green"]
        original = items.copy()
        self.assertEqual(last_index(items, "red"), 2)
        self.assertEqual(items, original)
        self.assertIsNone(last_index(items, "yellow"))
        self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
