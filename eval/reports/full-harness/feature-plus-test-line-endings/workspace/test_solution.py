import unittest

from solution import normalize


class NormalizeTests(unittest.TestCase):
    def test_ordinary_line_endings(self) -> None:
        for text, expected in (
            ("first\r\nsecond\rthird\nfourth", "first\nsecond\nthird\nfourth"),
            ("plain text", "plain text"),
            ("already\nnormalized\n", "already\nnormalized\n"),
            (" \t한글\x00\v\f\u2028\u2029\r\n ", " \t한글\x00\v\f\u2028\u2029\n "),
        ):
            with self.subTest(text=text):
                self.assertEqual(normalize(text), expected)

    def test_boundary_and_trailing_line_breaks(self) -> None:
        for text, expected in (
            ("\r", "\n"),
            ("\n", "\n"),
            ("\r\n", "\n"),
            ("\r\r\n", "\n\n"),
            ("\n\r", "\n\n"),
            ("\r\n\r\n\r\n", "\n\n\n"),
            ("\rstart\r\nend\r\n\r", "\nstart\nend\n\n"),
        ):
            with self.subTest(text=text):
                self.assertEqual(normalize(text), expected)

    def test_empty_input(self) -> None:
        self.assertEqual(normalize(""), "")


if __name__ == "__main__":
    unittest.main()
