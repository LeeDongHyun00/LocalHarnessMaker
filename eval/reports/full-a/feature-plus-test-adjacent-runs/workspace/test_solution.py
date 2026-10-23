"""Tests for the public run-length encoding API."""

import unittest

from solution import runs


class RunsTests(unittest.TestCase):
    def test_adjacent_and_nonadjacent_repeats(self) -> None:
        items = ["a", "a", "b", "b", "b", "a"]
        self.assertEqual(runs(items), [("a", 2), ("b", 3), ("a", 1)])

    def test_empty_input(self) -> None:
        self.assertEqual(runs([]), [])

    def test_boundary_inputs(self) -> None:
        cases = [
            (["one"], [("one", 1)]),
            (["same", "same", "same"], [("same", 3)]),
            (["a", "b", "c"], [("a", 1), ("b", 1), ("c", 1)]),
            (["", "", "x", ""], [("", 2), ("x", 1), ("", 1)]),
            (["é", "é", "猫"], [("é", 2), ("猫", 1)]),
        ]
        for items, expected in cases:
            with self.subTest(items=items):
                self.assertEqual(runs(items), expected)

    def test_input_is_not_mutated(self) -> None:
        items = ["a", "a", "b", "a"]
        original = items.copy()
        result = runs(items)
        self.assertEqual(items, original)
        result.append(("extra", 1))
        self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
