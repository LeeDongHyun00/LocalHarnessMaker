import unittest

from solution import parse_pairs


class ParsePairsTests(unittest.TestCase):
    def test_parses_records(self) -> None:
        text = "\n name = Alice \n \t\nname=Bob\n token = a=b=c \n empty = \n"
        self.assertEqual(
            parse_pairs(text),
            {"name": "Bob", "token": "a=b=c", "empty": ""},
        )

    def test_blank_input(self) -> None:
        for text in ("", "\n \t\r\n"):
            with self.subTest(text=text):
                self.assertEqual(parse_pairs(text), {})

    def test_missing_equals_raises(self) -> None:
        for text in ("missing", "valid=value\nmissing"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_pairs(text)

    def test_empty_key_raises(self) -> None:
        for text in ("=value", " \t =value", "valid=value\n = "):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_pairs(text)


if __name__ == "__main__":
    unittest.main()
