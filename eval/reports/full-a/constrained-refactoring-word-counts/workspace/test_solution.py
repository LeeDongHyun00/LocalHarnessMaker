import unittest

from solution import words, words_legacy


class WordsTests(unittest.TestCase):
    def test_whitespace_casefold_and_punctuation(self) -> None:
        text = "  Straße\tSTRASSE\nHello,\r\nHELLO,\vhello\fworld!\u2003WORLD!  "
        expected = {"strasse": 2, "hello,": 2, "hello": 1, "world!": 2}
        for function in (words, words_legacy):
            with self.subTest(function=function.__name__):
                result = function(text)
                self.assertIs(type(result), dict)
                self.assertEqual(result, expected)

    def test_empty_text(self) -> None:
        for function in (words, words_legacy):
            for text in ("", " \t\n\r\v\f\u2003"):
                with self.subTest(function=function.__name__, text=text):
                    self.assertEqual(function(text), {})

    def test_input_is_unchanged_and_results_are_independent(self) -> None:
        text = "One ONE two"
        for function in (words, words_legacy):
            with self.subTest(function=function.__name__):
                result = function(text)
                self.assertEqual(text, "One ONE two")
                result["one"] = 99
                self.assertEqual(function(text), {"one": 2, "two": 1})

    def test_invalid_inputs_keep_attribute_error_and_collections_unchanged(self) -> None:
        for function in (words, words_legacy):
            for value in (None, 42, ["One", "ONE"], {"One": 1}):
                with self.subTest(function=function.__name__, value=value):
                    original = value.copy() if isinstance(value, (list, dict)) else value
                    with self.assertRaises(AttributeError):
                        function(value)
                    self.assertEqual(value, original)

    def test_bytes_keep_casefold_error(self) -> None:
        for function in (words, words_legacy):
            with self.subTest(function=function.__name__):
                self.assertEqual(function(b""), {})
                with self.assertRaises(AttributeError):
                    function(b"word")


if __name__ == "__main__":
    unittest.main()
