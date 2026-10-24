import unittest

from solution import words


class WordsTests(unittest.TestCase):
    def test_whitespace_casefold_and_punctuation(self) -> None:
        self.assertEqual(
            words("  Straße\tSTRASSE\nHello!\r\nHELLO!\vhello\fHELLO\u2003"),
            {"strasse": 2, "hello!": 2, "hello": 2},
        )

    def test_empty_and_whitespace_only(self) -> None:
        for text in ("", " \t\n\r\v\f\u2003"):
            with self.subTest(text=text):
                self.assertEqual(words(text), {})


if __name__ == "__main__":
    unittest.main()
