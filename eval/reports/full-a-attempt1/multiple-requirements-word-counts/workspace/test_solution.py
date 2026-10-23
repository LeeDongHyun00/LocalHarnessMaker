"""Regression tests for the public words API."""

import unittest

from solution import words


class WordsTests(unittest.TestCase):
    def test_casefolds_and_counts_unicode_tokens(self) -> None:
        self.assertEqual(words("Straße STRASSE strasse Σ σ ς"),
                         {"strasse": 3, "σ": 3})

    def test_splits_arbitrary_whitespace(self) -> None:
        self.assertEqual(words("  One\ttwo\nONE\r\ntwo\vthree\fthree\u2003ONE  "),
                         {"one": 3, "two": 2, "three": 2})

    def test_preserves_punctuation(self) -> None:
        self.assertEqual(words("Hello, HELLO, hello! hello don't DON'T"),
                         {"hello,": 2, "hello!": 1, "hello": 1, "don't": 2})

    def test_empty_and_whitespace_only_text(self) -> None:
        for text in ("", " \t\n\r\v\f\u2003"):
            with self.subTest(text=text):
                self.assertEqual(words(text), {})

    def test_preserves_input_and_first_occurrence_order(self) -> None:
        text = "Zebra APPLE zebra Banana apple"
        original = text
        result = words(text)
        self.assertEqual(text, original)
        self.assertEqual(list(result.items()),
                         [("zebra", 2), ("apple", 2), ("banana", 1)])


if __name__ == "__main__":
    unittest.main()
