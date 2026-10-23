"""Regression tests for the public words API."""

import unittest

from solution import words


class WordsTests(unittest.TestCase):
    def test_counts_casefolded_tokens(self) -> None:
        self.assertEqual(
            words("Hello HELLO hello Straße STRASSE straße"),
            {"hello": 3, "strasse": 3},
        )

    def test_splits_arbitrary_whitespace(self) -> None:
        self.assertEqual(
            words(" \tOne\nTWO\r\none\vthree\fTWO\u2003three\u00a0"),
            {"one": 2, "two": 2, "three": 2},
        )

    def test_preserves_punctuation(self) -> None:
        self.assertEqual(
            words("Hi, HI, hi! hi (Hi)"),
            {"hi,": 2, "hi!": 1, "hi": 1, "(hi)": 1},
        )

    def test_empty_and_whitespace_only_text(self) -> None:
        for text in ("", " \t\n\r\v\f\u2003\u00a0"):
            with self.subTest(text=text):
                self.assertEqual(words(text), {})

    def test_preserves_input_and_first_occurrence_order(self) -> None:
        text = "Zulu ALPHA zulu Beta alpha Straße STRASSE"
        original = text
        result = words(text)
        self.assertEqual(text, original)
        self.assertEqual(
            list(result.items()),
            [("zulu", 2), ("alpha", 2), ("beta", 1), ("strasse", 2)],
        )


if __name__ == "__main__":
    unittest.main()
