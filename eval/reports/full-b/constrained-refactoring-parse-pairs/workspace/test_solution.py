import unittest

from solution import parse_pairs, parse_pairs_legacy


class ParsePairsTests(unittest.TestCase):
    def test_records_are_trimmed_and_last_key_wins(self) -> None:
        text = (
            "\n  name = first \r\n\t \r\n name = last \n"
            " token = one=two== \n empty = \n"
        )
        expected = {"name": "last", "token": "one=two==", "empty": ""}
        for parser in (parse_pairs, parse_pairs_legacy):
            with self.subTest(parser=parser.__name__):
                result = parser(text)
                self.assertIs(type(result), dict)
                self.assertEqual(result, expected)

    def test_empty_and_blank_inputs(self) -> None:
        for parser in (parse_pairs, parse_pairs_legacy):
            for text in ("", "\n", " \t\r\n\r\n", "\v\f"):
                with self.subTest(parser=parser.__name__, text=text):
                    self.assertEqual(parser(text), {})

    def test_invalid_records_raise_original_error(self) -> None:
        for parser in (parse_pairs, parse_pairs_legacy):
            for text in (
                "missing equals",
                "key:value",
                "=value",
                " \t = value",
                "valid=value\nbroken",
                "valid=value\n =bad",
            ):
                with self.subTest(parser=parser.__name__, text=text):
                    with self.assertRaisesRegex(ValueError, r"\Ainvalid record\Z"):
                        parser(text)

    def test_input_is_unchanged_and_results_are_independent(self) -> None:
        text = " name = original \nname = final\nempty=\n"
        original_lines = text.splitlines()
        for parser in (parse_pairs, parse_pairs_legacy):
            with self.subTest(parser=parser.__name__):
                first = parser(text)
                second = parser(text)
                self.assertIsNot(first, second)
                first["name"] = "changed"
                first["added"] = "value"
                self.assertEqual(second, {"name": "final", "empty": ""})
                self.assertEqual(text.splitlines(), original_lines)
                self.assertEqual(parser(text), second)


if __name__ == "__main__":
    unittest.main()
