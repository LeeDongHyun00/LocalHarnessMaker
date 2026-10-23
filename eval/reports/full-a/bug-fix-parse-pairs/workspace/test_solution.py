import unittest

from solution import parse_pairs


class ParsePairsTests(unittest.TestCase):
    def test_records_are_stripped_and_split_on_first_equals(self) -> None:
        text = '\n  name = first  \n \t\n name = last=value \n empty =   \n'
        self.assertEqual(parse_pairs(text), {'name': 'last=value', 'empty': ''})

    def test_empty_input_and_blank_lines(self) -> None:
        for text in ('', '\n \t\n'):
            with self.subTest(text=text):
                self.assertEqual(parse_pairs(text), {})

    def test_invalid_records_raise_value_error(self) -> None:
        for text in ('missing equals', '=value', '  =value', 'ok=value\nbad'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_pairs(text)


if __name__ == '__main__':
    unittest.main()
