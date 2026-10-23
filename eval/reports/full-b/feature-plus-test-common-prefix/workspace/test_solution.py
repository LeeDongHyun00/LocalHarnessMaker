"""Tests for the public longest common prefix API."""

import unittest

from solution import common


class CommonTests(unittest.TestCase):
    def test_ordinary_prefixes(self) -> None:
        cases = [
            (["flower", "flow", "flight"], "fl"),
            (["interspecies", "interstellar", "interstate"], "inters"),
            (["hello world", "hello there"], "hello "),
        ]
        for items, expected in cases:
            with self.subTest(items=items):
                self.assertEqual(common(items), expected)

    def test_prefix_boundaries(self) -> None:
        cases = [
            (["a", "ab", "abc"], "a"),
            (["prefix-long", "prefix", "prefix-longer"], "prefix"),
            (["same", "same", "same"], "same"),
            (["dog", "racecar", "car"], ""),
            (["ab", "ac", "ax"], "a"),
            (["abc", "abd", "xyz"], ""),
        ]
        for items, expected in cases:
            with self.subTest(items=items):
                self.assertEqual(common(items), expected)

    def test_case_sensitive_matching(self) -> None:
        self.assertEqual(common(["Flower", "flower"]), "")
        self.assertEqual(common(["preFix", "prefix"]), "pre")

    def test_empty_collection(self) -> None:
        self.assertEqual(common([]), "")

    def test_empty_strings(self) -> None:
        for items in (["", "abc"], ["abc", ""], ["", ""], ["abc", "abd", ""]):
            with self.subTest(items=items):
                self.assertEqual(common(items), "")

    def test_single_item(self) -> None:
        for item in ("alone", "a", "", " leading and trailing "):
            with self.subTest(item=item):
                self.assertEqual(common([item]), item)

    def test_unicode_characters(self) -> None:
        self.assertEqual(common(["café", "cafétéria"]), "café")
        self.assertEqual(common(["안녕하세요", "안녕히"]), "안녕")

    def test_input_is_not_mutated(self) -> None:
        for items in (["flight", "flower", "flow"], ["abc", ""], [], ["alone"]):
            with self.subTest(items=items):
                original = items.copy()
                common(items)
                self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
