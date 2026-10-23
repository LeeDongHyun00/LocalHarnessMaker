"""Tests for the public run-length encoding API."""

import unittest

from solution import runs


class RunsTests(unittest.TestCase):
    def test_adjacent_and_nonadjacent_values(self):
        items = ["a", "a", "b", "b", "b", "a"]
        original = items.copy()
        self.assertEqual(runs(items), [("a", 2), ("b", 3), ("a", 1)])
        self.assertEqual(items, original)

    def test_boundary_inputs(self):
        cases = [
            (["solo"], [("solo", 1)]),
            (["x", "x", "x"], [("x", 3)]),
            (["a", "b", "c"], [("a", 1), ("b", 1), ("c", 1)]),
            (["", "", "雪", "雪", ""], [("", 2), ("雪", 2), ("", 1)]),
        ]
        for items, expected in cases:
            with self.subTest(items=items):
                original = items.copy()
                self.assertEqual(runs(items), expected)
                self.assertEqual(items, original)

    def test_empty_input(self):
        items: list[str] = []
        self.assertEqual(runs(items), [])
        self.assertEqual(items, [])


if __name__ == "__main__":
    unittest.main()
