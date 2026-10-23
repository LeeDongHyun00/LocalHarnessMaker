import unittest

from solution import parse_pairs, parse_pairs_legacy


class ParsePairsTests(unittest.TestCase):
    def test_records_whitespace_duplicates_and_empty_values(self) -> None:
        text = "\n  name = first \n\t\nname = last\r\nvalue = a=b=c\nempty =  \n"
        original = text
        expected = {"name": "last", "value": "a=b=c", "empty": ""}
        for parser in (parse_pairs, parse_pairs_legacy):
            with self.subTest(parser=parser.__name__):
                result = parser(text)
                self.assertIsInstance(result, dict)
                self.assertEqual(result, expected)
                self.assertEqual(text, original)

    def test_invalid_records_preserve_error_message(self) -> None:
        for parser in (parse_pairs, parse_pairs_legacy):
            for text in ("missing equals", "=value", " \t = value", "ok=1\nbad"):
                with self.subTest(parser=parser.__name__, text=text):
                    with self.assertRaisesRegex(ValueError, "^invalid record$"):
                        parser(text)

    def test_blank_input_and_independent_results(self) -> None:
        for parser in (parse_pairs, parse_pairs_legacy):
            with self.subTest(parser=parser.__name__):
                self.assertEqual(parser(""), {})
                self.assertEqual(parser(" \n\t\r\n"), {})
                first = parser("key=value")
                first["key"] = "changed"
                self.assertEqual(parser("key=value"), {"key": "value"})


if __name__ == "__main__":
    unittest.main()
