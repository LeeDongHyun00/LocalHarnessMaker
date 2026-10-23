"""Regression coverage for the public words API."""

import unittest
from unittest.mock import call, patch

from solution import words, words_many


class WordsTests(unittest.TestCase):
    def test_counts_repeated_tokens_case_insensitively(self) -> None:
        self.assertEqual(words("Apple banana APPLE apple BANANA"),
                         {"apple": 3, "banana": 2})

    def test_splits_arbitrary_whitespace(self) -> None:
        self.assertEqual(words("  one\ttwo\n one\r\ntwo\vthree\fthree\u2003one  "),
                         {"one": 3, "two": 2, "three": 2})

    def test_uses_unicode_casefold(self) -> None:
        self.assertEqual(words("Straße STRASSE straße Σ σ ς"),
                         {"strasse": 3, "σ": 3})

    def test_preserves_punctuation(self) -> None:
        self.assertEqual(words("Hello, HELLO, hello! hello ..."),
                         {"hello,": 2, "hello!": 1, "hello": 1, "...": 1})

    def test_empty_and_whitespace_only_text(self) -> None:
        for text in ("", " ", "\t\n\r\v\f\u2003"):
            with self.subTest(text=text):
                self.assertEqual(words(text), {})

    def test_calls_return_independent_dictionaries(self) -> None:
        text = "Keep KEEP"
        first = words(text)
        first["keep"] = 99
        self.assertEqual(words(text), {"keep": 2})
        self.assertEqual(text, "Keep KEEP")


class WordsManyTests(unittest.TestCase):
    def test_returns_results_in_case_order_without_mutating_inputs(self) -> None:
        cases = [("Apple APPLE",), ("Straße STRASSE",), ("",), ("Hello! hello",)]
        original = cases.copy()

        self.assertEqual(words_many(cases), [
            {"apple": 2}, {"strasse": 2}, {}, {"hello!": 1, "hello": 1},
        ])
        self.assertEqual(cases, original)
        for case, saved in zip(cases, original):
            self.assertIs(case, saved)

    def test_empty_cases_do_not_call_words(self) -> None:
        with patch("solution.words") as single:
            self.assertEqual(words_many([]), [])
        single.assert_not_called()

    def test_unpacks_positional_arguments_without_mutating_them(self) -> None:
        argument = ["unchanged"]
        cases = [(argument, "second"), ()]
        with patch("solution.words", side_effect=["first", "second"]) as single:
            self.assertEqual(words_many(cases), ["first", "second"])
        self.assertEqual(single.call_args_list, [call(argument, "second"), call()])
        self.assertEqual(argument, ["unchanged"])
        self.assertIs(cases[0][0], argument)

    def test_propagates_first_exception_unchanged_and_stops(self) -> None:
        error = RuntimeError("first failure")
        cases = [("ok",), ("fails",), ("never called",)]
        original = cases.copy()
        with patch("solution.words", side_effect=[{"ok": 1}, error]) as single:
            with self.assertRaises(RuntimeError) as caught:
                words_many(cases)
        self.assertIs(caught.exception, error)
        self.assertEqual(single.call_args_list, [call("ok"), call("fails")])
        self.assertEqual(cases, original)

    def test_invalid_calls_preserve_words_errors(self) -> None:
        for case, error_type in (((), TypeError), (("a", "b"), TypeError),
                                 ((None,), AttributeError)):
            with self.subTest(case=case):
                with self.assertRaises(error_type):
                    words_many([case])

    def test_batch_results_are_independent(self) -> None:
        results = words_many([("Keep KEEP",), ("Keep KEEP",)])
        results[0]["keep"] = 99
        self.assertEqual(results[1], {"keep": 2})


if __name__ == "__main__":
    unittest.main()
