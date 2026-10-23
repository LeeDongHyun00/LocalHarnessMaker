import unittest

from solution import strip_prefix


class StripPrefixTests(unittest.TestCase):
    def test_removes_exactly_one_matching_prefix(self) -> None:
        self.assertEqual(strip_prefix("prefix-value", "prefix-"), "value")
        self.assertEqual(strip_prefix("ababvalue", "ab"), "abvalue")
        self.assertEqual(strip_prefix("aaaa", "a"), "aaa")
        self.assertEqual(strip_prefix("안녕하세요", "안녕"), "하세요")

    def test_nonmatching_prefix_leaves_text_unchanged(self) -> None:
        self.assertEqual(strip_prefix("value-prefix", "prefix"), "value-prefix")
        self.assertEqual(strip_prefix("Prefix-value", "prefix-"), "Prefix-value")
        self.assertEqual(strip_prefix("abacus", "abc"), "abacus")
        self.assertEqual(strip_prefix("ba-value", "ab"), "ba-value")

    def test_boundary_inputs(self) -> None:
        self.assertEqual(strip_prefix("value", "value"), "")
        self.assertEqual(strip_prefix("a", "a"), "")
        self.assertEqual(strip_prefix("value", "values"), "value")
        self.assertEqual(strip_prefix("  value", " "), " value")

    def test_empty_inputs(self) -> None:
        self.assertEqual(strip_prefix("value", ""), "value")
        self.assertEqual(strip_prefix("", "prefix"), "")
        self.assertEqual(strip_prefix("", ""), "")


if __name__ == "__main__":
    unittest.main()
