import unittest

from solution import parse_pairs, parse_pairs_legacy


class ParsePairsTests(unittest.TestCase):
    def test_records(self) -> None:
        text = '  first = old \n\n \t\n second = a=b=c \n first = new \nempty= \n'
        expected = {'first': 'new', 'second': 'a=b=c', 'empty': ''}
        for parser in (parse_pairs, parse_pairs_legacy):
            with self.subTest(parser=parser.__name__):
                self.assertEqual(parser(text), expected)

    def test_empty_and_blank_input(self) -> None:
        for parser in (parse_pairs, parse_pairs_legacy):
            for text in ('', '\n \t\r\n', '\r\n'):
                with self.subTest(parser=parser.__name__, text=text):
                    self.assertEqual(parser(text), {})

    def test_invalid_records(self) -> None:
        for parser in (parse_pairs, parse_pairs_legacy):
            for record in ('missing separator', '=value', ' \t =value'):
                for text in (record, 'valid=ok\n' + record):
                    with self.subTest(parser=parser.__name__, text=text):
                        with self.assertRaisesRegex(ValueError, '^invalid record$'):
                            parser(text)

    def test_input_unchanged_and_results_independent(self) -> None:
        text = ' key = value\r\nother=two\rfinal=three'
        original = text
        expected = {'key': 'value', 'other': 'two', 'final': 'three'}
        for parser in (parse_pairs, parse_pairs_legacy):
            with self.subTest(parser=parser.__name__):
                result = parser(text)
                self.assertIsInstance(result, dict)
                self.assertEqual(result, expected)
                result['key'] = 'changed'
                self.assertEqual(parser(text), expected)
                self.assertEqual(text, original)


if __name__ == '__main__':
    unittest.main()
