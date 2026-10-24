import inspect
import unittest

from solution import words, words_legacy


class WordsTests(unittest.TestCase):
    def test_whitespace_casefold_and_punctuation(self):
        text = "  Straße\tSTRASSE\nHello,\r\nHELLO,\vhello\fword!\u2003WORD!  "
        expected = {"strasse": 2, "hello,": 2, "hello": 1, "word!": 2}
        for function in (words, words_legacy):
            with self.subTest(function=function.__name__):
                result = function(text)
                self.assertIs(type(result), dict)
                self.assertEqual(result, expected)

    def test_empty_text(self):
        for function in (words, words_legacy):
            for text in ("", " \t\n\r\v\f\u2003"):
                with self.subTest(function=function.__name__, text=text):
                    self.assertEqual(function(text), {})

    def test_input_unchanged_and_results_independent(self):
        text = "One ONE two"
        for function in (words, words_legacy):
            with self.subTest(function=function.__name__):
                result = function(text)
                self.assertEqual(text, "One ONE two")
                result["one"] = 99
                self.assertEqual(function(text), {"one": 2, "two": 1})

    def test_original_invalid_input_errors_and_collection_immutability(self):
        for function in (words, words_legacy):
            for value in (None, 42, b"word", ["One", "two"], {"One": 1}):
                with self.subTest(function=function.__name__, value=value):
                    before = value.copy() if isinstance(value, (list, dict)) else value
                    with self.assertRaises(AttributeError):
                        function(value)
                    self.assertEqual(value, before)
            with self.assertRaises(TypeError):
                function()
            with self.assertRaises(TypeError):
                function("one", "two")

    def test_public_signatures_and_keyword_calls(self):
        for function in (words, words_legacy):
            with self.subTest(function=function.__name__):
                signature = inspect.signature(function)
                self.assertEqual(list(signature.parameters), ["text"])
                parameter = signature.parameters["text"]
                self.assertEqual(parameter.kind, inspect.Parameter.POSITIONAL_OR_KEYWORD)
                self.assertIs(parameter.default, inspect.Parameter.empty)
                self.assertIs(parameter.annotation, str)
                self.assertEqual(signature.return_annotation, dict[str, int])
                self.assertEqual(function(text="One ONE"), {"one": 2})


if __name__ == "__main__":
    unittest.main()
