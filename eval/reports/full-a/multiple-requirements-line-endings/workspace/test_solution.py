"""Regression tests for the public normalize API."""

import unittest

from solution import normalize


class NormalizeTests(unittest.TestCase):
    def test_normalizes_each_line_ending(self) -> None:
        for text, expected in (
            ("a\r\nb", "a\nb"),
            ("a\rb", "a\nb"),
            ("a\nb", "a\nb"),
            ("a\r\nb\rc\nd", "a\nb\nc\nd"),
        ):
            with self.subTest(text=text):
                self.assertEqual(normalize(text), expected)

    def test_preserves_repeated_and_trailing_line_breaks(self) -> None:
        for text, expected in (
            ("\r\r\n\n\r", "\n\n\n\n"),
            ("text\r\n\r\n", "text\n\n"),
            ("text\r", "text\n"),
            ("text\n\n", "text\n\n"),
            ("\n\r", "\n\n"),
        ):
            with self.subTest(text=text):
                self.assertEqual(normalize(text), expected)

    def test_preserves_all_other_characters(self) -> None:
        for text in ("", "plain text", " \t café 한글\x00\v\f\x85\u2028\u2029 "):
            with self.subTest(text=text):
                self.assertEqual(normalize(text), text)

    def test_preserves_input_values_and_collection_order(self) -> None:
        values = ["third\r", "first\r\n", "second\n", "third\r"]
        original = values.copy()

        results = [normalize(value) for value in values]

        self.assertEqual(values, original)
        self.assertEqual(results, ["third\n", "first\n", "second\n", "third\n"])


if __name__ == "__main__":
    unittest.main()
