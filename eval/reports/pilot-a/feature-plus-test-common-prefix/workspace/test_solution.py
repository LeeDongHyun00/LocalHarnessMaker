"""Tests for the public longest-common-prefix API."""

import unittest

from solution import common


class CommonTests(unittest.TestCase):
    def test_ordinary_prefixes(self) -> None:
        for items, expected in [
            (["flower", "flow", "flight"], "fl"),
            (["interview", "internet", "internal"], "inter"),
            (["dog", "racecar", "car"], ""),
            (["가나다", "가나무"], "가나"),
        ]:
            with self.subTest(items=items):
                self.assertEqual(common(items), expected)

    def test_boundary_inputs(self) -> None:
        for items, expected in [
            (["alone"], "alone"),
            (["same", "same"], "same"),
            (["prefix", "pre"], "pre"),
            (["pre", "prefix"], "pre"),
            (["Apple", "apple"], ""),
            (["abC", "abc"], "ab"),
            (["a", "ab", "ac"], "a"),
        ]:
            with self.subTest(items=items):
                self.assertEqual(common(items), expected)

    def test_empty_inputs(self) -> None:
        for items in [[], [""], ["", "abc"], ["abc", ""]]:
            with self.subTest(items=items):
                self.assertEqual(common(items), "")

    def test_input_is_not_mutated(self) -> None:
        items = ["flower", "flow", "flight"]
        original = items.copy()
        self.assertEqual(common(items), "fl")
        self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
