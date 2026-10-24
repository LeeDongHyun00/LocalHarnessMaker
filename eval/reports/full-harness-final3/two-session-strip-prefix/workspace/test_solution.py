import unittest
from unittest.mock import call, patch

from solution import strip_prefix, strip_prefix_many


class StripPrefixTests(unittest.TestCase):
    def test_matching_prefix(self) -> None:
        self.assertEqual(strip_prefix("prefix-value", "prefix-"), "value")

    def test_nonmatching_prefix(self) -> None:
        self.assertEqual(strip_prefix("value-prefix", "prefix"), "value-prefix")
        self.assertEqual(strip_prefix("short", "shorter"), "short")

    def test_empty_prefix(self) -> None:
        self.assertEqual(strip_prefix("value", ""), "value")
        self.assertEqual(strip_prefix("", ""), "")

    def test_repeated_prefix_removed_only_once(self) -> None:
        self.assertEqual(strip_prefix("preprevalue", "pre"), "prevalue")

    def test_prefix_is_not_a_character_set(self) -> None:
        self.assertEqual(strip_prefix("abbaa", "ab"), "baa")
        self.assertEqual(strip_prefix("ba-value", "ab"), "ba-value")

    def test_empty_text_and_full_match(self) -> None:
        self.assertEqual(strip_prefix("", "prefix"), "")
        self.assertEqual(strip_prefix("value", "value"), "")

    def test_unicode_prefix(self) -> None:
        self.assertEqual(strip_prefix("안녕세계", "안녕"), "세계")

    def test_batch_results_in_order_without_mutation(self) -> None:
        cases = [
            ("prefix-value", "prefix-"),
            ("unchanged", "other"),
            ("preprevalue", "pre"),
            ("안녕세계", "안녕"),
            ("value", ""),
            ("value", "value"),
        ]
        original = cases.copy()
        self.assertEqual(
            strip_prefix_many(cases),
            ["value", "unchanged", "prevalue", "세계", "value", ""],
        )
        self.assertEqual(cases, original)
        for actual, previous in zip(cases, original):
            self.assertIs(actual, previous)

    def test_empty_batch(self) -> None:
        cases = []
        self.assertEqual(strip_prefix_many(cases), [])
        self.assertEqual(cases, [])

    def test_batch_propagates_first_exception_unchanged(self) -> None:
        cases = [("first", "f"), ("second", "s"), ("third", "t")]
        original = cases.copy()
        error = ValueError("sentinel error")
        with patch("solution.strip_prefix", side_effect=["irst", error, "hird"]) as strip:
            with self.assertRaises(ValueError) as caught:
                strip_prefix_many(cases)
        self.assertIs(caught.exception, error)
        self.assertEqual(strip.call_args_list, [call("first", "f"), call("second", "s")])
        self.assertEqual(cases, original)

    def test_batch_invalid_arguments(self) -> None:
        for cases in [[("missing-prefix",)], [("text", None)]]:
            with self.subTest(cases=cases):
                with self.assertRaises(TypeError):
                    strip_prefix_many(cases)


if __name__ == "__main__":
    unittest.main()
