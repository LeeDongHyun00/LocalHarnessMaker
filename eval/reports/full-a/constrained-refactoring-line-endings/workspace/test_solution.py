import unittest

from solution import normalize, normalize_legacy


class NormalizeTests(unittest.TestCase):
    def test_newlines_and_other_characters_are_preserved(self) -> None:
        cases = (
            ('', ''),
            ('plain text', 'plain text'),
            ('a\r\nb\rc\nd\r\n', 'a\nb\nc\nd\n'),
            ('\r\n\r\n\r\n', '\n\n\n'),
            ('\r\r\n\n\r', '\n\n\n\n'),
            (' \t한글\x00\v\f\u0085\u2028\u2029\r\n\n',
             ' \t한글\x00\v\f\u0085\u2028\u2029\n\n'),
        )
        for function in (normalize, normalize_legacy):
            for original, expected in cases:
                with self.subTest(function=function.__name__, original=original):
                    result = function(original)
                    self.assertIsInstance(result, str)
                    self.assertEqual(result, expected)

    def test_input_collection_is_unchanged(self) -> None:
        for function in (normalize, normalize_legacy):
            originals = ['a\r\nb', '\r\n\r', 'c\n']
            snapshot = originals.copy()
            with self.subTest(function=function.__name__):
                self.assertEqual(
                    [function(text) for text in originals],
                    ['a\nb', '\n\n', 'c\n'],
                )
                self.assertEqual(originals, snapshot)

    def test_invalid_inputs_keep_existing_errors(self) -> None:
        for function in (normalize, normalize_legacy):
            for invalid in (None, 42, [], {}):
                with self.subTest(function=function.__name__, invalid=invalid):
                    with self.assertRaises(AttributeError):
                        function(invalid)
            with self.subTest(function=function.__name__, invalid=b'\r\n'):
                with self.assertRaises(TypeError):
                    function(b'\r\n')


if __name__ == '__main__':
    unittest.main()
