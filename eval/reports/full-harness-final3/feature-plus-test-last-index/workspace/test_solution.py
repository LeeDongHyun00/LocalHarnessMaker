"""Tests for the public last_index API."""

import unittest

from solution import last_index


class LastIndexTests(unittest.TestCase):
    def test_repeated_matches_and_absent_target(self):
        items = ["apple", "pear", "apple", "plum"]
        self.assertEqual(last_index(items, "apple"), 2)
        self.assertIsNone(last_index(items, "banana"))

    def test_boundary_positions(self):
        self.assertEqual(last_index(["apple", "pear"], "apple"), 0)
        self.assertEqual(last_index(["apple", "pear"], "pear"), 1)
        self.assertEqual(last_index(["apple"], "apple"), 0)
        self.assertIsNone(last_index(["apple"], "pear"))
        self.assertEqual(last_index(["apple", "apple"], "apple"), 1)

    def test_empty_input(self):
        self.assertIsNone(last_index([], "apple"))
        self.assertIsNone(last_index([], ""))

    def test_case_sensitive_and_empty_string_matches(self):
        self.assertEqual(last_index(["Apple", "apple", "Apple"], "apple"), 1)
        self.assertIsNone(last_index(["Apple"], "APPLE"))
        self.assertEqual(last_index(["", "apple", ""], ""), 2)

    def test_input_is_not_mutated(self):
        items = ["apple", "pear", "apple"]
        original = items.copy()
        last_index(items, "apple")
        self.assertEqual(items, original)
        last_index(items, "banana")
        self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
