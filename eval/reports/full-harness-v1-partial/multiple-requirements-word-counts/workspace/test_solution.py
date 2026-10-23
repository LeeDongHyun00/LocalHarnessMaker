import unittest

from solution import words


class WordsTests(unittest.TestCase):
    def test_arbitrary_whitespace_and_repeated_tokens(self) -> None:
        self.assertEqual(words(" one\ttwo\none\r\nthree\v two\f\u2003one "),
                         {"one": 3, "two": 2, "three": 1})

    def test_unicode_casefolding(self) -> None:
        self.assertEqual(words("Straße STRASSE straße Hello HELLO"),
                         {"strasse": 3, "hello": 2})

    def test_punctuation_is_retained(self) -> None:
        self.assertEqual(words("Hello, HELLO, hello hello! HELLO!"),
                         {"hello,": 2, "hello": 1, "hello!": 2})

    def test_empty_and_whitespace_only_text(self) -> None:
        for text in ("", " \t\n\r\v\f\u2003"):
            with self.subTest(text=text):
                self.assertEqual(words(text), {})

    def test_first_occurrence_order_after_casefolding(self) -> None:
        result = words("Zebra Straße APPLE STRASSE zebra banana")
        self.assertEqual(
            list(result.items()),
            [("zebra", 2), ("strasse", 2), ("apple", 1), ("banana", 1)],
        )

    def test_input_value_is_preserved(self) -> None:
        text = "  Zebra\tStraße!\nSTRASSE!  "
        self.assertEqual(words(text), {"zebra": 1, "strasse!": 2})
        self.assertEqual(text, "  Zebra\tStraße!\nSTRASSE!  ")

    def test_results_are_independent_between_calls(self) -> None:
        text = "Zebra APPLE zebra"
        first = words(text)
        second = words(text)
        self.assertIsNot(first, second)
        first.clear()
        first["changed"] = 99
        expected = [("zebra", 2), ("apple", 1)]
        self.assertEqual(list(second.items()), expected)
        self.assertEqual(list(words(text).items()), expected)
        self.assertEqual(text, "Zebra APPLE zebra")


if __name__ == "__main__":
    unittest.main()
