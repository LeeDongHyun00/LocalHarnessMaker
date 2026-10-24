import unittest

from solution import words


class WordsTests(unittest.TestCase):
    def test_arbitrary_whitespace(self) -> None:
        self.assertEqual(
            words("  One\ttwo\nONE\r\nthree\v two\fthree\u2003ONE  "),
            {"one": 3, "two": 2, "three": 2},
        )

    def test_unicode_casefolding(self) -> None:
        self.assertEqual(
            words("Straße STRASSE strasse Σ σ ς"),
            {"strasse": 3, "σ": 3},
        )

    def test_punctuation_is_retained(self) -> None:
        self.assertEqual(
            words("Hello, HELLO, hello hello! ..."),
            {"hello,": 2, "hello": 1, "hello!": 1, "...": 1},
        )

    def test_empty_and_whitespace_only(self) -> None:
        for text in ("", " ", "\t\n\r\v\f\u2003"):
            with self.subTest(text=text):
                self.assertEqual(words(text), {})

    def test_first_occurrence_order_and_input_preservation(self) -> None:
        text = "Zebra Apple ZEBRA banana APPLE"
        original = text
        result = words(text)
        self.assertEqual(list(result.items()), [("zebra", 2), ("apple", 2), ("banana", 1)])
        self.assertEqual(text, original)


if __name__ == "__main__":
    unittest.main()
