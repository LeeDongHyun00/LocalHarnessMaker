import unittest

from solution import strip_prefix


class StripPrefixTests(unittest.TestCase):
    def test_removes_exactly_one_matching_prefix(self) -> None:
        cases = [
            ("foobar", "foo", "bar"),
            ("foofoobar", "foo", "foobar"),
            ("oofbar", "foo", "oofbar"),
            ("bar", "foo", "bar"),
            ("foobar", "", "foobar"),
            ("foo", "foo", ""),
            ("", "foo", ""),
        ]
        for text, prefix, expected in cases:
            with self.subTest(text=text, prefix=prefix):
                self.assertEqual(strip_prefix(text, prefix), expected)


if __name__ == "__main__":
    unittest.main()
