"""Regression tests for the public normalize API."""

import unittest

from solution import normalize


class NormalizeTests(unittest.TestCase):
    def test_crlf_is_one_line_break(self) -> None:
        self.assertEqual(normalize('first\r\nsecond\r\n'), 'first\nsecond\n')

    def test_lone_cr_becomes_lf(self) -> None:
        self.assertEqual(normalize('\rfirst\rsecond\r'), '\nfirst\nsecond\n')

    def test_existing_lf_and_other_characters_are_preserved(self) -> None:
        for text in ('', 'plain text', '\n\n', ' \tα\x00\v\f\u2028\nend\n'):
            with self.subTest(text=text):
                self.assertEqual(normalize(text), text)

    def test_mixed_and_adjacent_breaks_preserve_count(self) -> None:
        self.assertEqual(normalize('a\r\r\nb\n\rc\r\n\r\n\r'),
                         'a\n\nb\n\nc\n\n\n')

    def test_normalizing_collection_preserves_inputs_and_order(self) -> None:
        values = ['third\r', 'first\r\n', 'second\n', 'third\r']
        original = values.copy()
        self.assertEqual([normalize(value) for value in values],
                         ['third\n', 'first\n', 'second\n', 'third\n'])
        self.assertEqual(values, original)


if __name__ == '__main__':
    unittest.main()
