import unittest

from solution import normalize


class NormalizeTests(unittest.TestCase):
    def test_converts_crlf_and_lone_cr(self):
        self.assertEqual(normalize("first\r\nsecond\rthird\nfourth"),
                         "first\nsecond\nthird\nfourth")

    def test_preserves_consecutive_and_trailing_line_breaks(self):
        for text, expected in (
            ("\r\r\n\n\r", "\n\n\n\n"),
            ("text\r\n\r\n", "text\n\n"),
            ("text\r", "text\n"),
            ("text\n\n", "text\n\n"),
        ):
            with self.subTest(text=text):
                self.assertEqual(normalize(text), expected)

    def test_preserves_other_characters_and_existing_lf(self):
        for text in ("", "plain text", "  café\t世界\x00\v\f\u0085\u2028\u2029  \n"):
            with self.subTest(text=text):
                self.assertEqual(normalize(text), text)

    def test_preserves_input_values_and_collection_order(self):
        texts = ["z\r", "a\r\nb", "m\n", "z\r"]
        original = texts.copy()
        self.assertEqual([normalize(text) for text in texts],
                         ["z\n", "a\nb", "m\n", "z\n"])
        self.assertEqual(texts, original)


if __name__ == "__main__":
    unittest.main()
