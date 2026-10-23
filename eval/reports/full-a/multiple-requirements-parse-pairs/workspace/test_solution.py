import unittest

from solution import parse_pairs


class ParsePairsTests(unittest.TestCase):
    def test_strips_keys_and_values_and_ignores_blank_lines(self) -> None:
        self.assertEqual(
            parse_pairs("\n  name = Alice Smith  \n \t\n\tcity\t= Seoul\t\n"),
            {"name": "Alice Smith", "city": "Seoul"},
        )

    def test_splits_only_at_first_equals_and_preserves_value_content(self) -> None:
        self.assertEqual(
            parse_pairs("formula = a=b==c\nspacing = a  b\nmarker=="),
            {"formula": "a=b==c", "spacing": "a  b", "marker": "="},
        )

    def test_allows_empty_values(self) -> None:
        self.assertEqual(parse_pairs("a=\nb=  \t"), {"a": "", "b": ""})

    def test_last_repeated_key_wins_without_reordering(self) -> None:
        self.assertEqual(
            list(parse_pairs("b=first\na=second\n b =last\nc=third").items()),
            [("b", "last"), ("a", "second"), ("c", "third")],
        )

    def test_rejects_missing_equals_and_empty_keys(self) -> None:
        for text in ("invalid", "valid=yes\ninvalid", "=value", " \t =value", "="):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_pairs(text)

    def test_empty_input_and_blank_lines(self) -> None:
        for text in ("", "\n", " \t\r\n\n"):
            with self.subTest(text=text):
                self.assertEqual(parse_pairs(text), {})

    def test_input_is_preserved_and_results_are_independent(self) -> None:
        text = " b = a=b \r\na=\r\n"
        original = text
        first = parse_pairs(text)
        first["b"] = "changed"
        self.assertEqual(text, original)
        self.assertEqual(list(parse_pairs(text).items()), [("b", "a=b"), ("a", "")])


if __name__ == "__main__":
    unittest.main()
