"""Regression tests for the public strip_prefix API."""

import unittest

from solution import strip_prefix


class StripPrefixTests(unittest.TestCase):
    def test_removes_exactly_one_matching_prefix(self) -> None:
        self.assertEqual(strip_prefix("prefix-value", "prefix-"), "value")
        self.assertEqual(strip_prefix("abcabcvalue", "abc"), "abcvalue")
        self.assertEqual(strip_prefix("aaaa", "a"), "aaa")
        self.assertEqual(strip_prefix("whole", "whole"), "")

    def test_nonmatching_prefix_does_not_strip_individual_characters(self) -> None:
        for text, prefix in [("ba-value", "ab"), ("ab-value", "abc"),
                             ("value-prefix", "prefix"), ("ab", "abc")]:
            with self.subTest(text=text, prefix=prefix):
                self.assertEqual(strip_prefix(text, prefix), text)

    def test_empty_text_and_prefix(self) -> None:
        self.assertEqual(strip_prefix("value", ""), "value")
        self.assertEqual(strip_prefix("", "prefix"), "")
        self.assertEqual(strip_prefix("", ""), "")

    def test_preserves_input_values_and_collection_order(self) -> None:
        texts = ["pre-z", "plain", "pre-pre-a", "pre-z"]
        original_texts = texts.copy()
        prefix = "pre-"
        results = [strip_prefix(text, prefix) for text in texts]
        self.assertEqual(results, ["z", "plain", "pre-a", "z"])
        self.assertEqual(texts, original_texts)
        self.assertEqual(prefix, "pre-")

    def test_unicode_prefix_is_matched_literally(self) -> None:
        self.assertEqual(strip_prefix("안녕안녕세계", "안녕"), "안녕세계")
        self.assertEqual(strip_prefix("éclair", "e"), "éclair")


if __name__ == "__main__":
    unittest.main()
