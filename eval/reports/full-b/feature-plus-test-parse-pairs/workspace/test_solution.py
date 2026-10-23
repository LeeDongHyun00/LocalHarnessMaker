"""Tests for the public parse_pairs API."""

import unittest

from solution import parse_pairs


class ParsePairsTests(unittest.TestCase):
    def test_ordinary_records(self) -> None:
        self.assertEqual(
            parse_pairs("name=Ada\nlanguage=Python"),
            {"name": "Ada", "language": "Python"},
        )

    def test_strips_sides_and_ignores_blank_lines(self) -> None:
        self.assertEqual(
            parse_pairs("\n \t\n  name \t=\t Ada Lovelace  \n\t\n"),
            {"name": "Ada Lovelace"},
        )

    def test_splits_only_on_first_equals(self) -> None:
        self.assertEqual(
            parse_pairs("expression = a=b=c\nequals=="),
            {"expression": "a=b=c", "equals": "="},
        )

    def test_last_repeated_key_wins_after_stripping(self) -> None:
        self.assertEqual(
            parse_pairs("key=first\nother=kept\n key = second\nkey=last"),
            {"key": "last", "other": "kept"},
        )

    def test_empty_values_are_allowed(self) -> None:
        self.assertEqual(
            parse_pairs("empty=\nwhitespace= \t\nrepeated=value\nrepeated="),
            {"empty": "", "whitespace": "", "repeated": ""},
        )

    def test_empty_and_blank_inputs(self) -> None:
        for text in ("", "\n", " \t", "\n \t\n\r\n"):
            with self.subTest(text=text):
                self.assertEqual(parse_pairs(text), {})

    def test_windows_line_endings(self) -> None:
        self.assertEqual(
            parse_pairs("first=one\r\n\r\nsecond=two\r\n"),
            {"first": "one", "second": "two"},
        )

    def test_missing_equals_raises_value_error(self) -> None:
        for text in ("invalid", "  invalid  ", "valid=value\ninvalid"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_pairs(text)

    def test_empty_key_raises_value_error(self) -> None:
        for text in ("=value", "=", " \t =value", "valid=value\n = "):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_pairs(text)


if __name__ == "__main__":
    unittest.main()
