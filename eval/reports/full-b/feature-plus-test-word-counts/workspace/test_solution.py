import unittest

from solution import words


class WordsTests(unittest.TestCase):
    def test_counts_repeated_words_case_insensitively(self) -> None:
        self.assertEqual(
            words("One two one THREE two three"),
            {"one": 2, "two": 2, "three": 2},
        )

    def test_splits_on_arbitrary_whitespace(self) -> None:
        self.assertEqual(
            words(" \talpha\nbeta\r\nalpha\vbeta\fgamma\u2003gamma\u00a0 "),
            {"alpha": 2, "beta": 2, "gamma": 2},
        )

    def test_uses_unicode_casefolding(self) -> None:
        self.assertEqual(
            words("Straße STRASSE straße Σ σ ς K k"),
            {"strasse": 3, "σ": 3, "k": 2},
        )

    def test_preserves_punctuation(self) -> None:
        self.assertEqual(
            words("Hello, hello HELLO! hello, can't CAN'T word-word word_word"),
            {
                "hello,": 2,
                "hello": 1,
                "hello!": 1,
                "can't": 2,
                "word-word": 1,
                "word_word": 1,
            },
        )

    def test_single_token(self) -> None:
        for text, expected in (("A", {"a": 1}), (" \t...\n", {"...": 1})):
            with self.subTest(text=text):
                self.assertEqual(words(text), expected)

    def test_empty_and_whitespace_only_inputs(self) -> None:
        for text in ("", " ", "\t\n\r\v\f", "\u2003\u00a0"):
            with self.subTest(text=text):
                self.assertEqual(words(text), {})


if __name__ == "__main__":
    unittest.main()
