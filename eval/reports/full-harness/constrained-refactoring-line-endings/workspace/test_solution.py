import unittest

from solution import normalize, normalize_legacy


class NormalizeTests(unittest.TestCase):
    def test_newline_normalization(self):
        cases = [
            ("", ""),
            ("a\r\nb\rc\nd", "a\nb\nc\nd"),
            ("\r\n\r\n\r\n\n\r", "\n\n\n\n\n"),
            ("text\r\n\r\n", "text\n\n"),
            ("text\r\r", "text\n\n"),
            ("text\n\n", "text\n\n"),
            (" \t한글\x00\v\f\u0085\u2028\u2029 ",
             " \t한글\x00\v\f\u0085\u2028\u2029 "),
        ]
        for function in (normalize, normalize_legacy):
            for original, expected in cases:
                with self.subTest(function=function.__name__, text=original):
                    result = function(original)
                    self.assertIsInstance(result, str)
                    self.assertEqual(result, expected)

    def test_input_collection_is_unchanged(self):
        original = ["a\r\nb", "c\rd\n", "\r\n"]
        for function in (normalize, normalize_legacy):
            with self.subTest(function=function.__name__):
                values = original.copy()
                self.assertEqual(
                    [function(value) for value in values],
                    ["a\nb", "c\nd\n", "\n"],
                )
                self.assertEqual(values, original)
                with self.assertRaises(AttributeError):
                    function(values)
                self.assertEqual(values, original)

    def test_invalid_input_errors(self):
        for function in (normalize, normalize_legacy):
            for value in (None, 42):
                with self.subTest(function=function.__name__, value=value):
                    with self.assertRaises(AttributeError):
                        function(value)
            with self.subTest(function=function.__name__, value=b"a\r\nb"):
                with self.assertRaises(TypeError):
                    function(b"a\r\nb")


if __name__ == "__main__":
    unittest.main()
