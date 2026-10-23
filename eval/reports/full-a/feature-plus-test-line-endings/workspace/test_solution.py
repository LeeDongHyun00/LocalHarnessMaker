"""Tests for the public newline normalization API."""

import unittest

from solution import normalize


class NormalizeTests(unittest.TestCase):
    def test_ordinary_inputs(self) -> None:
        cases = [
            ("first\r\nsecond\r\nthird", "first\nsecond\nthird"),
            ("first\rsecond\rthird", "first\nsecond\nthird"),
            ("first\nsecond\nthird", "first\nsecond\nthird"),
            ("a\r\nb\rc\nd", "a\nb\nc\nd"),
            (" \t café 世界\u2028\u2029\x00 ", " \t café 世界\u2028\u2029\x00 "),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(normalize(source), expected)

    def test_boundary_and_trailing_line_breaks(self) -> None:
        cases = [
            ("\r", "\n"),
            ("\n", "\n"),
            ("\r\n", "\n"),
            ("\r\r\n", "\n\n"),
            ("\n\r", "\n\n"),
            ("\r\n\r\n\r\n", "\n\n\n"),
            ("\r\ntext\r\n\r\n", "\ntext\n\n"),
            ("text\n\n", "text\n\n"),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(normalize(source), expected)

    def test_empty_and_no_line_breaks(self) -> None:
        for source in ("", "text", " ", "\t"):
            with self.subTest(source=source):
                self.assertEqual(normalize(source), source)


if __name__ == "__main__":
    unittest.main()
