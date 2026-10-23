import inspect
import unittest

from solution import normalize, normalize_legacy


class NormalizeTests(unittest.TestCase):
    def test_normalizes_line_endings(self):
        cases = (
            ('', ''),
            ('plain text', 'plain text'),
            ('a\nb\n', 'a\nb\n'),
            ('a\r\nb\r\n', 'a\nb\n'),
            ('a\rb\r', 'a\nb\n'),
            ('\r\n\r\n\n\r', '\n\n\n\n'),
            ('a\r\rb\n\rc\r\n\n', 'a\n\nb\n\nc\n\n'),
        )
        for function in (normalize, normalize_legacy):
            for original, expected in cases:
                with self.subTest(function=function.__name__, text=original):
                    self.assertEqual(function(original), expected)

    def test_preserves_other_characters_and_input_collection(self):
        originals = [
            ' \t\x00\v\f\x85\u2028\u2029\u00e9\ud55c\U0001f600 \r\n\r\n',
            '\n\n',
        ]
        snapshot = originals.copy()
        expected = [
            ' \t\x00\v\f\x85\u2028\u2029\u00e9\ud55c\U0001f600 \n\n',
            '\n\n',
        ]
        for function in (normalize, normalize_legacy):
            with self.subTest(function=function.__name__):
                self.assertEqual([function(text) for text in originals], expected)
                self.assertEqual(originals, snapshot)

    def test_preserves_type_errors_and_rejected_collections(self):
        for function in (normalize, normalize_legacy):
            for value, error in (
                (None, AttributeError),
                (42, AttributeError),
                (['a\r\n'], AttributeError),
                ({'text': 'a\r\n'}, AttributeError),
                (b'a\r\n', TypeError),
            ):
                with self.subTest(function=function.__name__, value=value):
                    snapshot = value.copy() if isinstance(value, (list, dict)) else value
                    with self.assertRaises(error):
                        function(value)
                    self.assertEqual(value, snapshot)

    def test_preserves_signatures_and_return_types(self):
        for function in (normalize, normalize_legacy):
            with self.subTest(function=function.__name__):
                signature = inspect.signature(function)
                self.assertEqual(list(signature.parameters), ['text'])
                parameter = signature.parameters['text']
                self.assertIs(parameter.annotation, str)
                self.assertEqual(parameter.kind, inspect.Parameter.POSITIONAL_OR_KEYWORD)
                self.assertIs(parameter.default, inspect.Parameter.empty)
                self.assertIs(signature.return_annotation, str)
                self.assertIs(type(function(text='a\r\n')), str)


if __name__ == '__main__':
    unittest.main()
