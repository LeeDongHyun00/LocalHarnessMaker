"""Tests for the public run-length encoding API."""

import unittest

from solution import runs


class RunsTests(unittest.TestCase):
    def test_adjacent_runs_and_nonadjacent_repeats(self) -> None:
        items = ["a", "a", "b", "b", "b", "a"]
        original = items.copy()
        self.assertEqual(runs(items), [("a", 2), ("b", 3), ("a", 1)])
        self.assertEqual(items, original)

    def test_empty_input(self) -> None:
        self.assertEqual(runs([]), [])

    def test_boundary_inputs(self) -> None:
        cases = [
            (["only"], [("only", 1)]),
            (["x", "x", "x"], [("x", 3)]),
            (["a", "b", "a", "b"], [("a", 1), ("b", 1), ("a", 1), ("b", 1)]),
            (["", "", "é", "é", ""], [("", 2), ("é", 2), ("", 1)]),
        ]
        for items, expected in cases:
            with self.subTest(items=items):
                original = items.copy()
                self.assertEqual(runs(items), expected)
                self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
