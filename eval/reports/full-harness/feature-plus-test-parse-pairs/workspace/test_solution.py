"""Tests for the public key/value parser."""

import unittest

from solution import parse_pairs


class ParsePairsTests(unittest.TestCase):
    def test_ordinary_records_and_repeated_keys(self) -> None:
        text = " name = Alice \n city=Seoul\nname = Bob "
        self.assertEqual(parse_pairs(text), {"name": "Bob", "city": "Seoul"})

    def test_first_equals_and_empty_values(self) -> None:
        self.assertEqual(
            parse_pairs("expression = a=b=c\nempty=\nspaces=   \nequals=="),
            {"expression": "a=b=c", "empty": "", "spaces": "", "equals": "="},
        )

    def test_empty_and_blank_inputs(self) -> None:
        for text in ("", "\n", " \t\r\n\n  "):
            with self.subTest(text=text):
                self.assertEqual(parse_pairs(text), {})

    def test_blank_lines_and_crlf(self) -> None:
        self.assertEqual(
            parse_pairs("\r\n a=1\r\n \t\r\nb=2\r\n"),
            {"a": "1", "b": "2"},
        )

    def test_invalid_records(self) -> None:
        for text in ("missing", "=value", " \t =value", "valid=yes\ninvalid"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_pairs(text)


if __name__ == "__main__":
    unittest.main()
