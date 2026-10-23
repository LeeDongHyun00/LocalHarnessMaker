import unittest

from solution import words


class WordsTests(unittest.TestCase):
    def test_casefold_whitespace_and_punctuation(self) -> None:
        self.assertEqual(
            words("  Straße\tSTRASSE\nHello! hello!\r\nhello\u2003HELLO  "),
            {"strasse": 2, "hello!": 2, "hello": 2},
        )

    def test_empty_text(self) -> None:
        for text in ("", " \t\n\r\u2003"):
            with self.subTest(text=text):
                self.assertEqual(words(text), {})


if __name__ == "__main__":
    unittest.main()
