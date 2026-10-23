"""Regression tests for the public normalize API."""

import unittest
from unittest.mock import call, patch

from solution import normalize, normalize_many


class NormalizeTests(unittest.TestCase):
    def test_crlf_becomes_one_lf(self) -> None:
        self.assertEqual(normalize("first\r\nsecond\r\n"), "first\nsecond\n")

    def test_lone_cr_becomes_lf(self) -> None:
        self.assertEqual(normalize("\rfirst\rsecond\r"), "\nfirst\nsecond\n")

    def test_existing_lf_and_other_characters_are_preserved(self) -> None:
        text = " \tCafé\x00\v\f\u0085\u2028\u2029🙂\nnext\n\n"
        self.assertEqual(normalize(text), text)

    def test_mixed_endings_preserve_each_line_break(self) -> None:
        self.assertEqual(normalize("a\r\n\rb\n\r\r\nc"), "a\n\nb\n\n\nc")

    def test_empty_and_plain_text(self) -> None:
        for text in ("", "plain text", " \t "):
            with self.subTest(text=text):
                self.assertEqual(normalize(text), text)

    def test_trailing_line_breaks_are_not_stripped(self) -> None:
        for ending in ("\n", "\r", "\r\n"):
            with self.subTest(ending=ending):
                self.assertEqual(normalize("text" + ending * 3), "text\n\n\n")

    def test_input_is_unchanged_and_result_is_idempotent(self) -> None:
        text = "a\r\nb\rc\n"
        result = normalize(text)
        self.assertEqual(text, "a\r\nb\rc\n")
        self.assertEqual(normalize(result), result)


class NormalizeManyTests(unittest.TestCase):
    def test_batch_results_follow_case_order_without_mutation(self) -> None:
        cases = [("b\r\nc",), ("",), ("a\rz\n",), ("plain",)]
        original = cases.copy()
        self.assertEqual(normalize_many(cases), ["b\nc", "", "a\nz\n", "plain"])
        self.assertEqual(cases, original)
        for case, saved_case in zip(cases, original):
            self.assertIs(case, saved_case)

    def test_empty_batch_does_not_call_normalize(self) -> None:
        with patch("solution.normalize") as normalize_mock:
            self.assertEqual(normalize_many([]), [])
            normalize_mock.assert_not_called()

    def test_tuples_supply_positional_arguments_without_mutation(self) -> None:
        argument = ["a\r\nb"]
        cases = [(argument, "second"), ()]
        original = cases.copy()
        with patch("solution.normalize", side_effect=["first", "second"]) as mock:
            self.assertEqual(normalize_many(cases), ["first", "second"])
            self.assertEqual(mock.call_args_list, [call(argument, "second"), call()])
            self.assertIs(mock.call_args_list[0].args[0], argument)
        self.assertEqual(argument, ["a\r\nb"])
        self.assertEqual(cases, original)

    def test_first_exception_is_propagated_unchanged_and_stops_batch(self) -> None:
        error = ValueError("first failure")
        cases = [("ok",), ("bad",), ("never called",)]
        original = cases.copy()
        with patch("solution.normalize", side_effect=["ok", error, RuntimeError()]) as mock:
            with self.assertRaises(ValueError) as caught:
                normalize_many(cases)
            self.assertIs(caught.exception, error)
            self.assertEqual(mock.call_args_list, [call("ok"), call("bad")])
        self.assertEqual(cases, original)

    def test_invalid_arguments_preserve_normalize_errors(self) -> None:
        for case, error_type in (((), TypeError), (("a", "b"), TypeError), ((None,), AttributeError)):
            with self.subTest(case=case):
                with self.assertRaises(error_type):
                    normalize_many([case])


if __name__ == "__main__":
    unittest.main()
