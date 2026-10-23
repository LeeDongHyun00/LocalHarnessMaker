import unittest

from solution import normalize


class NormalizeTests(unittest.TestCase):
    def test_converts_crlf_and_lone_cr(self) -> None:
        self.assertEqual(normalize('a\r\nb\rc\nd'), 'a\nb\nc\nd')

    def test_preserves_lf_and_other_characters(self) -> None:
        text = ' \t한글\x00\v\f\u0085\u2028\u2029\nnext \t\n'
        self.assertEqual(normalize(text), text)
        self.assertEqual(normalize(''), '')

    def test_preserves_line_break_count_and_trailing_newlines(self) -> None:
        cases = [
            ('\r\n', '\n', 1),
            ('\r', '\n', 1),
            ('\n', '\n', 1),
            ('a\r\r\n\n\r', 'a\n\n\n\n', 4),
            ('a\r\n\r\n', 'a\n\n', 2),
            ('\n\r', '\n\n', 2),
        ]
        for text, expected, count in cases:
            with self.subTest(text=text):
                result = normalize(text)
                self.assertEqual(result, expected)
                self.assertEqual(result.count('\n'), count)

    def test_preserves_input_values_and_collection_order(self) -> None:
        texts = ['z\r', 'a\r\n', 'm\n', '']
        original = texts.copy()
        results = [normalize(text) for text in texts]
        self.assertEqual(texts, original)
        self.assertEqual(results, ['z\n', 'a\n', 'm\n', ''])


if __name__ == '__main__':
    unittest.main()
