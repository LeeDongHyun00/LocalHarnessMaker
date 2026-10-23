import unittest

from solution import last_index


class LastIndexTests(unittest.TestCase):
    def test_returns_last_match_without_mutating_input(self):
        items = ["a", "b", "a"]
        self.assertEqual(last_index(items, "a"), 2)
        self.assertEqual(items, ["a", "b", "a"])

    def test_absent_empty_and_case_sensitive(self):
        self.assertIsNone(last_index([], "a"))
        self.assertIsNone(last_index(["a"], "b"))
        self.assertIsNone(last_index(["A"], "a"))
        self.assertEqual(last_index(["a", "A"], "a"), 0)
