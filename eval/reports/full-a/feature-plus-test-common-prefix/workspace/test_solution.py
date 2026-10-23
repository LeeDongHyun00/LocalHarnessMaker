"""Tests for the public common-prefix API."""

import unittest

from solution import common


class CommonTests(unittest.TestCase):
    def test_ordinary_prefixes(self) -> None:
        for items, expected in [
            (["flower", "flow", "flight"], "fl"),
            (["prefix", "pre", "prepare"], "pre"),
            (["same", "same"], "same"),
            (["café", "caféteria"], "café"),
        ]:
            with self.subTest(items=items):
                self.assertEqual(common(items), expected)

    def test_boundary_inputs(self) -> None:
        for items, expected in [
            (["single"], "single"),
            (["dog", "racecar", "car"], ""),
            (["Alpha", "alpha"], ""),
            (["a", "ab"], "a"),
            (["abc", "abd", "ax"], "a"),
        ]:
            with self.subTest(items=items):
                self.assertEqual(common(items), expected)

    def test_empty_inputs(self) -> None:
        for items in [[], [""], ["", "abc"], ["abc", ""], ["", ""]]:
            with self.subTest(items=items):
                self.assertEqual(common(items), "")

    def test_input_is_not_mutated(self) -> None:
        items = ["flower", "flow", "flight"]
        original = items.copy()
        self.assertEqual(common(items), "fl")
        self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
