import unittest

from solution import parse_pairs


class ParsePairsTests(unittest.TestCase):
    def test_strips_fields_and_preserves_internal_whitespace(self) -> None:
        text = "  first key \t=  two  words\tinside  \n\tsecond = value \t"
        original = text

        self.assertEqual(
            parse_pairs(text),
            {"first key": "two  words\tinside", "second": "value"},
        )
        self.assertEqual(text, original)

    def test_splits_only_on_first_equals_sign(self) -> None:
        self.assertEqual(
            parse_pairs("equation = left=right\nleading==value\ntrailing=value="),
            {"equation": "left=right", "leading": "=value", "trailing": "value="},
        )

    def test_allows_empty_values(self) -> None:
        self.assertEqual(parse_pairs("empty=\nblank= \t "), {"empty": "", "blank": ""})

    def test_ignores_blank_lines(self) -> None:
        self.assertEqual(
            parse_pairs("\n \t\n first=one\n\t\nsecond=two\n\n"),
            {"first": "one", "second": "two"},
        )
        for text in ("", "\n", " \t\n\r\n "):
            with self.subTest(text=text):
                self.assertEqual(parse_pairs(text), {})

    def test_repeated_keys_keep_first_appearance_order_and_last_value(self) -> None:
        result = parse_pairs(
            "beta=old\nalpha=one\n beta = new=two \ngamma=three\nalpha=final"
        )

        self.assertEqual(
            list(result.items()),
            [("beta", "new=two"), ("alpha", "final"), ("gamma", "three")],
        )

    def test_rejects_missing_equals_sign(self) -> None:
        for text in ("missing", "valid=value\nmissing", " \tmissing \t"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_pairs(text)

    def test_rejects_empty_keys(self) -> None:
        for text in ("=value", " \t =value", "=", " \t = \t", "valid=value\n=bad"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_pairs(text)


if __name__ == "__main__":
    unittest.main()
