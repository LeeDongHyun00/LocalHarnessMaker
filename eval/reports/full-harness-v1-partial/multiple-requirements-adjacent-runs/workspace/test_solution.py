"""Regression tests for the public run-length encoding API."""

import unittest

from solution import runs


class RunsTests(unittest.TestCase):
    def test_empty_input(self) -> None:
        self.assertEqual(runs([]), [])

    def test_single_value(self) -> None:
        self.assertEqual(runs(["hello"]), [("hello", 1)])

    def test_adjacent_repetitions(self) -> None:
        self.assertEqual(
            runs(["a", "a", "b", "b", "b", "c", "c"]),
            [("a", 2), ("b", 3), ("c", 2)],
        )

    def test_nonadjacent_values_remain_separate_and_ordered(self) -> None:
        self.assertEqual(
            runs(["b", "b", "a", "b", "b", "a"]),
            [("b", 2), ("a", 1), ("b", 2), ("a", 1)],
        )

    def test_exact_string_values_are_preserved(self) -> None:
        self.assertEqual(
            runs(["", "", " A ", "a", "A", "\n", "한글", "한글"]),
            [("", 2), (" A ", 1), ("a", 1), ("A", 1), ("\n", 1), ("한글", 2)],
        )

    def test_input_is_not_mutated(self) -> None:
        items = ["z", "z", "a", "z"]
        original = items.copy()
        self.assertEqual(runs(items), [("z", 2), ("a", 1), ("z", 1)])
        self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
