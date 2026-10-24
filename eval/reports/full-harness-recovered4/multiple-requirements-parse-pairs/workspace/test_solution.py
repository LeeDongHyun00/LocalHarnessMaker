import unittest

from solution import parse_pairs


class ParsePairsTests(unittest.TestCase):
    def test_splits_first_equals_and_strips_both_sides(self) -> None:
        self.assertEqual(
            parse_pairs("  name = Alice Smith  \n expression = a=b=c \n"),
            {"name": "Alice Smith", "expression": "a=b=c"},
        )

    def test_ignores_blank_lines_and_accepts_empty_values(self) -> None:
        self.assertEqual(parse_pairs("\n \t\nempty=\nspace=   \n"),
                         {"empty": "", "space": ""})
        self.assertEqual(parse_pairs(""), {})
        self.assertEqual(parse_pairs(" \t\n\n"), {})

    def test_duplicate_keys_replace_values_without_reordering(self) -> None:
        result = parse_pairs("b=first\na=second\n b = final\nc=third")
        self.assertEqual(list(result.items()),
                         [("b", "final"), ("a", "second"), ("c", "third")])

    def test_invalid_records_raise_value_error(self) -> None:
        for text in ("missing", "=value", " \t =value", "valid=ok\nbad"):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_pairs(text)

    def test_preserves_input_and_value_contents(self) -> None:
        text = "path = /a/b==c\r\nmessage = hello  world\r\n"
        original = text
        self.assertEqual(parse_pairs(text),
                         {"path": "/a/b==c", "message": "hello  world"})
        self.assertEqual(text, original)


if __name__ == "__main__":
    unittest.main()
