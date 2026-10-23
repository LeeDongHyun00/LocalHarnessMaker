import unittest

from solution import strip_prefix


class StripPrefixTests(unittest.TestCase):
    def test_removes_one_matching_prefix(self) -> None:
        self.assertEqual(strip_prefix("prefix-value", "prefix-"), "value")
        self.assertEqual(strip_prefix("same", "same"), "")

    def test_keeps_repeated_prefixes_after_the_first(self) -> None:
        self.assertEqual(strip_prefix("ababvalue", "ab"), "abvalue")
        self.assertEqual(strip_prefix("aaa", "a"), "aa")

    def test_nonmatching_prefix_leaves_text_unchanged(self) -> None:
        for text, prefix in [
            ("cabinet", "abc"),
            ("abacus", "abc"),
            ("ab", "abc"),
            ("Prefix-value", "prefix-"),
            ("value-prefix", "prefix"),
        ]:
            with self.subTest(text=text, prefix=prefix):
                self.assertEqual(strip_prefix(text, prefix), text)

    def test_empty_prefix_and_empty_text(self) -> None:
        self.assertEqual(strip_prefix("value", ""), "value")
        self.assertEqual(strip_prefix("", "prefix"), "")
        self.assertEqual(strip_prefix("", ""), "")

    def test_preserves_whitespace_and_unicode(self) -> None:
        self.assertEqual(strip_prefix("  value  ", " "), " value  ")
        self.assertEqual(strip_prefix("한한글", "한"), "한글")

    def test_preserves_input_values_and_collection_order(self) -> None:
        cases = [
            ("pre-z", "pre-"),
            ("pre-apre-a", "pre-"),
            ("cab", "abc"),
            ("pre-z", "pre-"),
            ("a", ""),
        ]
        original_cases = cases.copy()

        results = [strip_prefix(text, prefix) for text, prefix in cases]

        self.assertEqual(results, ["z", "apre-a", "cab", "z", "a"])
        self.assertEqual(cases, original_cases)


if __name__ == "__main__":
    unittest.main()
