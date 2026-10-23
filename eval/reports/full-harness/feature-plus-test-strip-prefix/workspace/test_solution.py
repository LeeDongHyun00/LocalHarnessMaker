import unittest

from solution import strip_prefix


class StripPrefixTests(unittest.TestCase):
    def test_matching_prefix(self):
        self.assertEqual(strip_prefix("hello world", "hello "), "world")
        self.assertEqual(strip_prefix("café au lait", "café "), "au lait")

    def test_removes_only_one_complete_prefix(self):
        self.assertEqual(strip_prefix("abcabcvalue", "abc"), "abcvalue")
        self.assertEqual(strip_prefix("abacus", "abc"), "abacus")
        self.assertEqual(strip_prefix("cabvalue", "abc"), "cabvalue")

    def test_nonmatching_prefix(self):
        self.assertEqual(strip_prefix("hello world", "world"), "hello world")
        self.assertEqual(strip_prefix("Hello", "hello"), "Hello")

    def test_boundary_inputs(self):
        self.assertEqual(strip_prefix("same", "same"), "")
        self.assertEqual(strip_prefix("short", "shorter"), "short")
        self.assertEqual(strip_prefix("a", "a"), "")

    def test_empty_inputs(self):
        self.assertEqual(strip_prefix("text", ""), "text")
        self.assertEqual(strip_prefix("", "prefix"), "")
        self.assertEqual(strip_prefix("", ""), "")


if __name__ == "__main__":
    unittest.main()
