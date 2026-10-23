"""Tests for the public word-counting API."""

import unittest

from solution import words


class WordsTests(unittest.TestCase):
    def test_ordinary_counts(self) -> None:
        self.assertEqual(words("Apple banana apple APPLE"), {"apple": 3, "banana": 1})

    def test_arbitrary_whitespace_and_unicode_casefolding(self) -> None:
        self.assertEqual(
            words(" \tStraße\nSTRASSE\r\nΣ\vς\fσ\u2003end\u00a0"),
            {"strasse": 2, "σ": 3, "end": 1},
        )

    def test_punctuation_remains_in_tokens(self) -> None:
        self.assertEqual(
            words("Hello, HELLO, hello hello! ..."),
            {"hello,": 2, "hello": 1, "hello!": 1, "...": 1},
        )

    def test_single_token(self) -> None:
        self.assertEqual(words("WORD"), {"word": 1})

    def test_empty_and_whitespace_only(self) -> None:
        for text in ("", " ", "\t\n\r\v\f\u2003\u00a0"):
            with self.subTest(text=text):
                self.assertEqual(words(text), {})


if __name__ == "__main__":
    unittest.main()
