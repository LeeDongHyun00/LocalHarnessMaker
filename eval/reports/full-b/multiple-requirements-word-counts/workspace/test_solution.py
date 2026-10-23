import unittest

from solution import words


class WordsTests(unittest.TestCase):
    def test_empty_and_whitespace_only_text(self) -> None:
        for text in ("", "   ", "\t\n\r\v\f\u00a0\u2003"):
            with self.subTest(text=text):
                self.assertEqual(words(text), {})

    def test_counts_tokens_after_casefolding(self) -> None:
        self.assertEqual(
            words("Apple banana APPLE apple BANANA"),
            {"apple": 3, "banana": 2},
        )

    def test_unicode_casefolding(self) -> None:
        self.assertEqual(
            words("Straße STRASSE straße Σ σ ς K K k"),
            {"strasse": 3, "σ": 3, "k": 3},
        )

    def test_arbitrary_whitespace(self) -> None:
        self.assertEqual(
            words(" red\tblue\nred\rgreen\vblue\fred\u00a0green\u2003blue "),
            {"red": 3, "blue": 3, "green": 2},
        )

    def test_punctuation_remains_part_of_tokens(self) -> None:
        self.assertEqual(
            words("Hello, HELLO, hello HELLO hello! HeLLo!"),
            {"hello,": 2, "hello": 2, "hello!": 2},
        )

    def test_preserves_input_and_first_occurrence_order(self) -> None:
        text = "Zebra APPLE zebra Banana apple CHERRY banana"
        original = text

        result = words(text)

        self.assertEqual(text, original)
        self.assertEqual(
            list(result.items()),
            [("zebra", 2), ("apple", 2), ("banana", 2), ("cherry", 1)],
        )


if __name__ == "__main__":
    unittest.main()
