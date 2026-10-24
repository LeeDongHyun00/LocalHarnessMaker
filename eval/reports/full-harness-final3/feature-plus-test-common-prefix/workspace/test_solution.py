"""Tests for the public common-prefix API."""

import unittest

from solution import common


class CommonTests(unittest.TestCase):
    def test_ordinary_prefixes(self) -> None:
        for items, expected in [
            (["flower", "flow", "flight"], "fl"),
            (["interview", "internet", "internal"], "inter"),
            (["café", "caféine"], "café"),
            (["two words", "two worlds"], "two wor"),
        ]:
            with self.subTest(items=items):
                self.assertEqual(common(items), expected)

    def test_boundary_inputs(self) -> None:
        for items, expected in [
            (["solo"], "solo"),
            (["same", "same"], "same"),
            (["prefix", "pre", "prepare"], "pre"),
            (["dog", "cat"], ""),
            (["Alpha", "alpha"], ""),
            (["abC", "abc"], "ab"),
        ]:
            with self.subTest(items=items):
                self.assertEqual(common(items), expected)

    def test_empty_inputs(self) -> None:
        for items in ([], [""], ["", "abc"], ["abc", ""], ["", ""]):
            with self.subTest(items=items):
                self.assertEqual(common(items), "")

    def test_input_is_not_mutated(self) -> None:
        items = ["flower", "flight", "flow"]
        original = items.copy()
        self.assertEqual(common(items), "fl")
        self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
