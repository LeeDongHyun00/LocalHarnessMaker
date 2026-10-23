import unittest

from solution import normalize


class NormalizeTests(unittest.TestCase):
    def test_normalize_line_endings(self) -> None:
        cases = (
            ("", ""),
            ("\ntext \tβ\u2028more\n\n", "\ntext \tβ\u2028more\n\n"),
            ("\r\nfirst\rsecond\nthird\r\n\r", "\nfirst\nsecond\nthird\n\n"),
            ("\r\n\r\n", "\n\n"),
            ("\r\r", "\n\n"),
        )
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(normalize(text), expected)


if __name__ == "__main__":
    unittest.main()
