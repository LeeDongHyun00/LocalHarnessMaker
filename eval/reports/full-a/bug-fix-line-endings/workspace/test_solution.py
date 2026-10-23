import unittest

from solution import normalize


class NormalizeTests(unittest.TestCase):
    def test_preserves_content_and_line_breaks(self) -> None:
        cases = [
            ("", ""),
            ("  café\t", "  café\t"),
            ("a\r\nb\rc\n", "a\nb\nc\n"),
            ("\r\n\r\n\r\n\n\r", "\n\n\n\n\n"),
            ("a\r\r\nb", "a\n\nb"),
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(normalize(text), expected)


if __name__ == "__main__":
    unittest.main()
