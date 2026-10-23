"""Tests for the public words API."""

import unittest

from solution import words


class WordsTests(unittest.TestCase):
    def test_counts_repeated_tokens_case_insensitively(self) -> None:
        self.assertEqual(words("Hello world HELLO World hello"), {"hello": 3, "world": 2})

    def test_arbitrary_whitespace(self) -> None:
        self.assertEqual(words(" \talpha\nbeta\ralpha\vbeta\fgamma\u2003alpha "),
                         {"alpha": 3, "beta": 2, "gamma": 1})

    def test_punctuation_remains_part_of_tokens(self) -> None:
        self.assertEqual(words("Hello, hello HELLO, hello! ..."),
                         {"hello,": 2, "hello": 1, "hello!": 1, "...": 1})

    def test_unicode_casefolding(self) -> None:
        self.assertEqual(words("Straße STRASSE Σ σ ς"), {"strasse": 2, "σ": 3})

    def test_single_token(self) -> None:
        self.assertEqual(words("A"), {"a": 1})

    def test_empty_and_whitespace_only(self) -> None:
        for text in ("", " ", "\t\n\r\v\f\u2003"):
            with self.subTest(text=text):
                self.assertEqual(words(text), {})


if __name__ == "__main__":
    unittest.main()
