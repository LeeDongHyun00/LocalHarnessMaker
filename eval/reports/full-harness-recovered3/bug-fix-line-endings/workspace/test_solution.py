import unittest

from solution import normalize


class NormalizeTests(unittest.TestCase):
    def test_normalize_line_endings(self) -> None:
        cases = [
            ("", ""),
            ("plain text\t café\u2028", "plain text\t café\u2028"),
            ("a\r\nb\rc\n", "a\nb\nc\n"),
            ("\r\n\r\n", "\n\n"),
            ("\r\r\n\n\r", "\n\n\n\n"),
            ("a\n\n", "a\n\n"),
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(normalize(text), expected)


if __name__ == "__main__":
    unittest.main()
