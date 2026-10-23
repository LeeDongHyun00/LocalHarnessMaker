import unittest

from solution import words, words_legacy


class WordsTests(unittest.TestCase):
    def test_counts_tokens_across_arbitrary_whitespace(self) -> None:
        text = "  One\ttwo\nONE\r\ntwo\vthree\fTHREE\u00a0one\u2003two\u2028three  "
        for function in (words, words_legacy):
            with self.subTest(function=function.__name__):
                self.assertEqual(function(text), {"one": 3, "two": 3, "three": 3})

    def test_casefolds_unicode_and_preserves_punctuation(self) -> None:
        text = "Straße STRASSE ß SS İ i\u0307 Hello, HELLO, hello! hello"
        expected = {
            "strasse": 2,
            "ss": 2,
            "i\u0307": 2,
            "hello,": 2,
            "hello!": 1,
            "hello": 1,
        }
        for function in (words, words_legacy):
            with self.subTest(function=function.__name__):
                self.assertEqual(function(text), expected)

    def test_empty_and_whitespace_only_text(self) -> None:
        for function in (words, words_legacy):
            for text in ("", " \t\n\r\v\f\u00a0\u2003\u2028"):
                with self.subTest(function=function.__name__, text=text):
                    self.assertEqual(function(text), {})

    def test_returns_independent_plain_dictionaries(self) -> None:
        for function in (words, words_legacy):
            for text in ("", "Word word"):
                with self.subTest(function=function.__name__, text=text):
                    first = function(text)
                    second = function(text)
                    self.assertIs(type(first), dict)
                    self.assertIsNot(first, second)
                    first["changed"] = 1
                    self.assertNotIn("changed", second)

    def test_does_not_mutate_shared_token_collection(self) -> None:
        tokens = ["ONE", "two", "One"]

        class SharedTokensText(str):
            def split(self, sep: str | None = None, maxsplit: int = -1) -> list[str]:
                return tokens

        text = SharedTokensText("ONE two One")
        for function in (words, words_legacy):
            with self.subTest(function=function.__name__):
                self.assertEqual(function(text), {"one": 2, "two": 1})
                self.assertEqual(text, "ONE two One")
                self.assertEqual(tokens, ["ONE", "two", "One"])

    def test_preserves_attribute_errors_for_invalid_inputs(self) -> None:
        for function in (words, words_legacy):
            for value in (None, 42, [], {}, b"word"):
                with self.subTest(function=function.__name__, value=value):
                    with self.assertRaises(AttributeError):
                        function(value)


if __name__ == "__main__":
    unittest.main()
