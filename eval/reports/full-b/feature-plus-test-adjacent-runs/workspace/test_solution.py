"""Tests for the public run-length encoding API."""

import unittest

from solution import runs


class RunsTests(unittest.TestCase):
    def test_adjacent_equal_strings_are_counted(self) -> None:
        self.assertEqual(
            runs(["a", "a", "b", "b", "b", "c"]),
            [("a", 2), ("b", 3), ("c", 1)],
        )

    def test_nonadjacent_equal_strings_form_separate_runs(self) -> None:
        self.assertEqual(
            runs(["a", "b", "a", "a", "b"]),
            [("a", 1), ("b", 1), ("a", 2), ("b", 1)],
        )

    def test_boundary_inputs(self) -> None:
        cases = [
            (["a"], [("a", 1)]),
            (["a", "a", "a"], [("a", 3)]),
            (["a", "b", "c"], [("a", 1), ("b", 1), ("c", 1)]),
        ]
        for items, expected in cases:
            with self.subTest(items=items):
                self.assertEqual(runs(items), expected)

    def test_empty_input(self) -> None:
        self.assertEqual(runs([]), [])

    def test_empty_and_unicode_strings(self) -> None:
        self.assertEqual(
            runs(["", "", "\ud55c", "\ud55c", ""]),
            [("", 2), ("\ud55c", 2), ("", 1)],
        )

    def test_input_is_not_mutated(self) -> None:
        items = ["a", "a", "b", "a"]
        original = items.copy()

        self.assertEqual(runs(items), [("a", 2), ("b", 1), ("a", 1)])
        self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
