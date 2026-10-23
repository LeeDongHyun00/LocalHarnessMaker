import unittest

from solution import strip_prefix


class StripPrefixTests(unittest.TestCase):
    def test_removes_exactly_one_matching_prefix(self) -> None:
        cases = [
            ("prefix-value", "prefix-", "value"),
            ("ababvalue", "ab", "abvalue"),
            ("ba-value", "ab", "ba-value"),
            ("abc", "abcd", "abc"),
            ("value", "", "value"),
            ("", "prefix", ""),
            ("same", "same", ""),
        ]
        for text, prefix, expected in cases:
            with self.subTest(text=text, prefix=prefix):
                self.assertEqual(strip_prefix(text, prefix), expected)


if __name__ == "__main__":
    unittest.main()
