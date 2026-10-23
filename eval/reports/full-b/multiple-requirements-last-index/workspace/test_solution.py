"""Regression tests for the public last_index API."""

import unittest

from solution import last_index


class LastIndexTests(unittest.TestCase):
    def test_returns_last_index_for_repeated_values(self) -> None:
        self.assertEqual(last_index(["pear", "apple", "pear", "plum"], "pear"), 2)
        self.assertEqual(last_index(["pear", "pear", "pear"], "pear"), 2)

    def test_returns_index_for_single_match(self) -> None:
        items = ["pear", "apple", "plum"]
        for expected, target in enumerate(items):
            with self.subTest(target=target):
                self.assertEqual(last_index(items, target), expected)
        self.assertEqual(last_index(["pear"], "pear"), 0)

    def test_returns_none_when_target_is_absent(self) -> None:
        self.assertIsNone(last_index(["pear", "apple", "plum"], "orange"))

    def test_empty_input_returns_none(self) -> None:
        self.assertIsNone(last_index([], "pear"))
        self.assertIsNone(last_index([], ""))

    def test_matching_is_case_sensitive(self) -> None:
        items = ["Apple", "apple", "Apple"]
        self.assertEqual(last_index(items, "Apple"), 2)
        self.assertEqual(last_index(items, "apple"), 1)
        self.assertIsNone(last_index(items, "APPLE"))

    def test_preserves_input_values_and_order(self) -> None:
        for target, expected in (("Alpha", 4), ("", 3), (" beta ", 5), ("missing", None)):
            with self.subTest(target=target):
                items = ["zebra", "Alpha", "alpha", "", "Alpha", " beta ", "Zebra"]
                original = items.copy()
                self.assertEqual(last_index(items, target), expected)
                self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
