"""Public regression tests for word counting."""

import unittest
from unittest.mock import call, patch

from solution import words, words_many


class WordsTests(unittest.TestCase):
    def test_counts_repeated_words(self):
        self.assertEqual(words("apple banana apple"), {"apple": 2, "banana": 1})

    def test_splits_arbitrary_whitespace(self):
        self.assertEqual(words(" \tOne\ntwo\r\none\vthree\ftwo\u2003one "),
                         {"one": 3, "two": 2, "three": 1})

    def test_casefolds_unicode(self):
        self.assertEqual(words("Straße STRASSE straße"), {"strasse": 3})

    def test_preserves_punctuation(self):
        self.assertEqual(words("Hello, HELLO, hello! hello"),
                         {"hello,": 2, "hello!": 1, "hello": 1})

    def test_empty_and_whitespace_only(self):
        for text in ("", " \t\r\n\v\f\u2003"):
            with self.subTest(text=text):
                self.assertEqual(words(text), {})

    def test_input_is_unchanged_and_results_are_independent(self):
        text = "One ONE"
        first = words(text)
        first["one"] = 99
        self.assertEqual(text, "One ONE")
        self.assertEqual(words(text), {"one": 2})


class WordsManyTests(unittest.TestCase):
    def test_batch_preserves_order_and_inputs(self):
        cases = [("One ONE",), ("Straße STRASSE!",), ("",)]
        original = cases.copy()
        expected = [words(*case) for case in cases]

        self.assertEqual(words_many(cases), expected)
        self.assertEqual(cases, original)

    def test_batch_empty(self):
        with patch("solution.words") as single:
            self.assertEqual(words_many([]), [])
        single.assert_not_called()

    def test_batch_propagates_first_exception_unchanged(self):
        first_error = ValueError("first failure")
        cases = [("one",), ("two",), ("three",)]
        with patch("solution.words", side_effect=[{}, first_error, RuntimeError()]) as single:
            with self.assertRaises(ValueError) as caught:
                words_many(cases)

        self.assertIs(caught.exception, first_error)
        self.assertEqual(single.call_args_list, [call("one"), call("two")])

    def test_batch_unpacks_positional_arguments_without_mutation(self):
        argument = ["mutable"]
        cases = [(argument, "second")]
        with patch("solution.words", return_value={"result": 1}) as single:
            self.assertEqual(words_many(cases), [{"result": 1}])

        single.assert_called_once_with(argument, "second")
        self.assertIs(single.call_args.args[0], argument)
        self.assertEqual(argument, ["mutable"])
        self.assertEqual(cases, [(argument, "second")])


if __name__ == "__main__":
    unittest.main()
