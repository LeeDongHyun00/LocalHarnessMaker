"""Regression tests for the public common API."""

import unittest

from solution import common


class CommonTests(unittest.TestCase):
    def test_empty_input(self) -> None:
        self.assertEqual(common([]), "")

    def test_single_item(self) -> None:
        for item in ("", "flower", " AbC🌸 "):
            with self.subTest(item=item):
                self.assertEqual(common([item]), item)

    def test_longest_common_prefix(self) -> None:
        cases = [
            (["flower", "flow", "flight"], "fl"),
            (["abc", "abcdef", "abcd"], "abc"),
            (["abcdef", "abcd", "abc"], "abc"),
            (["same", "same"], "same"),
            (["dog", "racecar", "car"], ""),
            (["prefix", ""], ""),
            (["", "prefix"], ""),
            (["a b!x", "a b!y"], "a b!"),
            (["🌸café", "🌸cafeteria"], "🌸caf"),
        ]
        for items, expected in cases:
            with self.subTest(items=items):
                self.assertEqual(common(items), expected)

    def test_case_sensitive_matching(self) -> None:
        self.assertEqual(common(["Flower", "flower"]), "")
        self.assertEqual(common(["abC", "abc"]), "ab")

    def test_preserves_input_values_and_order(self) -> None:
        items = ["flight", "flower", "flow", "flower"]
        original = items.copy()
        self.assertEqual(common(items), "fl")
        self.assertEqual(items, original)
        for actual, previous in zip(items, original):
            self.assertIs(actual, previous)


if __name__ == "__main__":
    unittest.main()
