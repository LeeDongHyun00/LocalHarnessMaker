"""Tests for the public parse_pairs API."""

import unittest

from solution import parse_pairs


class ParsePairsTests(unittest.TestCase):
    def test_ordinary_records_and_whitespace(self) -> None:
        self.assertEqual(
            parse_pairs(" name = Alice \n\n age=30\n\t\ncity = Seoul \n"),
            {"name": "Alice", "age": "30", "city": "Seoul"},
        )

    def test_first_equals_empty_values_and_repeated_keys(self) -> None:
        self.assertEqual(
            parse_pairs("token=a=b=c\nempty=\nblank=   \n key=old\nkey = new"),
            {"token": "a=b=c", "empty": "", "blank": "", "key": "new"},
        )
        self.assertEqual(parse_pairs("key=old\nkey="), {"key": ""})

    def test_empty_inputs(self) -> None:
        for text in ("", "\n", " \t\n\r\n  "):
            with self.subTest(text=text):
                self.assertEqual(parse_pairs(text), {})

    def test_single_record_and_windows_newlines(self) -> None:
        self.assertEqual(parse_pairs("a=b"), {"a": "b"})
        self.assertEqual(parse_pairs("a=1\r\nb=2\r\n"), {"a": "1", "b": "2"})

    def test_invalid_records(self) -> None:
        for text in ("missing equals", "=value", " \t =value", "=", "a=1\nbad"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_pairs(text)


if __name__ == "__main__":
    unittest.main()
