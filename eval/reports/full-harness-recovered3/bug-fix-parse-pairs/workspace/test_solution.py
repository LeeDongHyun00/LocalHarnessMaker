import unittest

from solution import parse_pairs


class ParsePairsTests(unittest.TestCase):
    def test_records(self) -> None:
        text = '\n  name = first \n \t\n name = last \n token = a=b=c \n empty = \t\n'
        self.assertEqual(
            parse_pairs(text),
            {'name': 'last', 'token': 'a=b=c', 'empty': ''},
        )

    def test_blank_input(self) -> None:
        for text in ('', '\n \t\n'):
            with self.subTest(text=text):
                self.assertEqual(parse_pairs(text), {})

    def test_invalid_records(self) -> None:
        for text in ('missing equals', '=value', ' \t =value', 'ok=yes\nbad'):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    parse_pairs(text)


if __name__ == '__main__':
    unittest.main()
