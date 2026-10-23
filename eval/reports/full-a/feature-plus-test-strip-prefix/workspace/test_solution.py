"""Tests for the public strip_prefix API."""

import unittest

from solution import strip_prefix


class StripPrefixTests(unittest.TestCase):
    def test_matching_prefix(self) -> None:
        self.assertEqual(strip_prefix("hello world", "hello "), "world")
        self.assertEqual(strip_prefix("café noir", "café "), "noir")

    def test_removes_exactly_one_prefix(self) -> None:
        self.assertEqual(strip_prefix("ababab", "ab"), "abab")
        self.assertEqual(strip_prefix("aaab", "aa"), "ab")

    def test_nonmatching_prefix_leaves_text_unchanged(self) -> None:
        for text, prefix in (
            ("hello", "world"),
            ("hello", "Hello"),
            ("hello", "hello world"),
            ("bahello", "ab"),
            ("world hello", "hello"),
        ):
            with self.subTest(text=text, prefix=prefix):
                self.assertEqual(strip_prefix(text, prefix), text)

    def test_boundary_and_empty_inputs(self) -> None:
        for text, prefix, expected in (
            ("hello", "hello", ""),
            ("x", "x", ""),
            ("hello", "", "hello"),
            ("", "hello", ""),
            ("", "", ""),
        ):
            with self.subTest(text=text, prefix=prefix):
                self.assertEqual(strip_prefix(text, prefix), expected)


if __name__ == "__main__":
    unittest.main()
