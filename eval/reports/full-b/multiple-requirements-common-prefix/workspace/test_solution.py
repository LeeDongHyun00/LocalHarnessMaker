"""Regression tests for the public common API."""

import unittest

from solution import common


class CommonTests(unittest.TestCase):
    def test_longest_common_prefix(self) -> None:
        self.assertEqual(common(["flower", "flow", "flight"]), "fl")
        self.assertEqual(
            common(["interspecies", "interstellar", "interstate"]), "inters"
        )

    def test_empty_input(self) -> None:
        self.assertEqual(common([]), "")

    def test_single_item(self) -> None:
        for item in ("", "single item", "Mixed Case", "café"):
            with self.subTest(item=item):
                self.assertEqual(common([item]), item)

    def test_shortest_item_limits_prefix(self) -> None:
        for items in (
            ["app", "apple", "application"],
            ["apple", "app", "application"],
            ["apple", "application", "app"],
        ):
            with self.subTest(items=items):
                self.assertEqual(common(items), "app")

    def test_empty_item_prevents_common_prefix(self) -> None:
        for items in (["", "abc"], ["abc", ""], ["abc", "", "abcd"]):
            with self.subTest(items=items):
                self.assertEqual(common(items), "")

    def test_common_substring_is_not_a_prefix(self) -> None:
        self.assertEqual(common(["dog", "racecar", "car"]), "")
        self.assertEqual(common(["abc", "xbc"]), "")

    def test_matching_is_case_sensitive(self) -> None:
        self.assertEqual(common(["Apple", "apple"]), "")
        self.assertEqual(common(["abCd", "abcd"]), "ab")

    def test_unicode_characters(self) -> None:
        self.assertEqual(common(["café", "cafè"]), "caf")
        self.assertEqual(common(["한글abc", "한글xyz"]), "한글")
        self.assertEqual(common(["éclair", "e\u0301clair"]), "")

    def test_identical_items(self) -> None:
        self.assertEqual(common(["same", "same", "same"]), "same")

    def test_input_values_and_order_are_preserved(self) -> None:
        for items, expected in (
            (["flower", "flight", "flow", "flight"], "fl"),
            (["zebra", "apple", "zebra"], ""),
            (["single"], "single"),
            ([], ""),
        ):
            with self.subTest(items=items):
                original = items.copy()
                self.assertEqual(common(items), expected)
                self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
