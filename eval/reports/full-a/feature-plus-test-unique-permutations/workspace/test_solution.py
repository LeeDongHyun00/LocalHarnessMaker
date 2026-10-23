"""Tests for the public permutations API."""

import math
import unittest

from solution import permutations


class PermutationsTests(unittest.TestCase):
    def test_ordinary_input_is_sorted(self) -> None:
        self.assertEqual(
            permutations("cba"), ["abc", "acb", "bac", "bca", "cab", "cba"]
        )

    def test_repeated_characters_are_distinct(self) -> None:
        self.assertEqual(permutations("aba"), ["aab", "aba", "baa"])

    def test_empty_input(self) -> None:
        self.assertEqual(permutations(""), [""])

    def test_single_character_and_all_identical_characters(self) -> None:
        self.assertEqual(permutations("x"), ["x"])
        self.assertEqual(permutations("aaaaaaa"), ["aaaaaaa"])

    def test_maximum_length_with_unique_characters(self) -> None:
        text = "gfedcba"
        result = permutations(text)
        self.assertEqual(len(result), math.factorial(7))
        self.assertEqual(len(set(result)), len(result))
        self.assertEqual(result, sorted(result))
        self.assertEqual(result[0], "abcdefg")
        self.assertEqual(result[-1], "gfedcba")
        self.assertTrue(all(sorted(item) == sorted(text) for item in result))
        self.assertEqual(text, "gfedcba")

    def test_case_spaces_and_unicode_use_lexicographic_order(self) -> None:
        self.assertEqual(permutations("aA"), ["Aa", "aA"])
        self.assertEqual(permutations(" a"), [" a", "a "])
        self.assertEqual(permutations("éa"), ["aé", "éa"])


if __name__ == "__main__":
    unittest.main()
