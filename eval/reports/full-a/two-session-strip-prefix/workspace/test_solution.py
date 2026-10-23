"""Regression tests for the public strip_prefix API."""

import unittest
from unittest.mock import call, patch

from solution import strip_prefix, strip_prefix_many


class StripPrefixTests(unittest.TestCase):
    def test_removes_one_matching_prefix(self) -> None:
        self.assertEqual(strip_prefix("prefix-value", "prefix-"), "value")
        self.assertEqual(strip_prefix("same", "same"), "")

    def test_nonmatching_prefix_leaves_text_unchanged(self) -> None:
        self.assertEqual(strip_prefix("value-prefix", "prefix"), "value-prefix")
        self.assertEqual(strip_prefix("Prefix-value", "prefix-"), "Prefix-value")
        self.assertEqual(strip_prefix("", "prefix"), "")

    def test_empty_prefix_leaves_text_unchanged(self) -> None:
        self.assertEqual(strip_prefix("value", ""), "value")
        self.assertEqual(strip_prefix("", ""), "")

    def test_repeated_prefix_is_removed_only_once(self) -> None:
        self.assertEqual(strip_prefix("abcabcvalue", "abc"), "abcvalue")

    def test_prefix_is_not_a_set_of_characters(self) -> None:
        self.assertEqual(strip_prefix("abacus", "ab"), "acus")
        self.assertEqual(strip_prefix("ba-value", "ab"), "ba-value")
        self.assertEqual(strip_prefix("a-value", "ab"), "a-value")

    def test_unicode_prefix(self) -> None:
        self.assertEqual(strip_prefix("안녕안녕세계", "안녕"), "안녕세계")


class StripPrefixManyTests(unittest.TestCase):
    def test_batch_preserves_order_and_inputs(self) -> None:
        cases = [
            ("prefix-value", "prefix-"),
            ("abcabcvalue", "abc"),
            ("value-prefix", "prefix"),
            ("same", "same"),
            ("value", ""),
            ("", "prefix"),
            ("안녕안녕세계", "안녕"),
        ]
        original = cases.copy()
        self.assertEqual(
            strip_prefix_many(cases),
            ["value", "abcvalue", "value-prefix", "", "value", "", "안녕세계"],
        )
        self.assertEqual(cases, original)
        for case, original_case in zip(cases, original):
            self.assertIs(case, original_case)

    def test_empty_batch(self) -> None:
        cases = []
        with patch("solution.strip_prefix") as single:
            self.assertEqual(strip_prefix_many(cases), [])
        single.assert_not_called()
        self.assertEqual(cases, [])

    def test_first_exception_is_propagated_unchanged_and_stops_batch(self) -> None:
        failure = ValueError("original failure")
        text, prefix = ["text"], ["prefix"]
        cases = [("abc", "a"), (text, prefix), ("later", "l")]
        original = cases.copy()
        with patch("solution.strip_prefix", side_effect=["bc", failure]) as single:
            with self.assertRaises(ValueError) as caught:
                strip_prefix_many(cases)
        self.assertIs(caught.exception, failure)
        self.assertEqual(single.call_args_list, [call("abc", "a"), call(text, prefix)])
        self.assertIs(single.call_args.args[0], text)
        self.assertIs(single.call_args.args[1], prefix)
        self.assertEqual(cases, original)
        self.assertEqual(text, ["text"])
        self.assertEqual(prefix, ["prefix"])

    def test_invalid_argument_count_and_types_raise(self) -> None:
        for case in [(), ("text",), ("text", "t", "extra"), ("text", None)]:
            with self.subTest(case=case):
                with self.assertRaises(TypeError):
                    strip_prefix_many([case])


if __name__ == "__main__":
    unittest.main()
