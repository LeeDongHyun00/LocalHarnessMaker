"""Tests for the public line-ending normalization API."""

import unittest

from solution import normalize


class NormalizeTests(unittest.TestCase):
    def test_normalizes_ordinary_line_endings(self) -> None:
        cases = (
            ("first\r\nsecond\r\nthird", "first\nsecond\nthird"),
            ("first\rsecond\rthird", "first\nsecond\nthird"),
            ("first\r\nsecond\rthird\nfourth", "first\nsecond\nthird\nfourth"),
        )
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(normalize(text), expected)

    def test_preserves_existing_lf(self) -> None:
        text = "\nfirst\n\nsecond\n"
        self.assertEqual(normalize(text), text)

    def test_preserves_other_characters(self) -> None:
        text = " \tHello, 세계!\x00\v\f\x85\u2028\u2029\r\n  fin\t "
        expected = " \tHello, 세계!\x00\v\f\x85\u2028\u2029\n  fin\t "
        self.assertEqual(normalize(text), expected)

    def test_preserves_boundary_and_consecutive_line_breaks(self) -> None:
        cases = (
            ("\r", "\n"),
            ("\r\n", "\n"),
            ("\n", "\n"),
            ("\r\r\n", "\n\n"),
            ("\n\r", "\n\n"),
            ("\r\n\r\n\r\n", "\n\n\n"),
            ("\r\ntext\r\n\r", "\ntext\n\n"),
            ("text\r\n", "text\n"),
            ("text\r", "text\n"),
        )
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(normalize(text), expected)

    def test_preserves_text_without_line_breaks(self) -> None:
        for text in ("x", "ordinary text", "  padded text  "):
            with self.subTest(text=text):
                self.assertEqual(normalize(text), text)

    def test_empty_input(self) -> None:
        self.assertEqual(normalize(""), "")


if __name__ == "__main__":
    unittest.main()
