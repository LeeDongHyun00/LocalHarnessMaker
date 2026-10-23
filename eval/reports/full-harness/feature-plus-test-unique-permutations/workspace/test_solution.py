"""Tests for the public permutation API."""

import math
import unittest

from solution import permutations


class PermutationsTests(unittest.TestCase):
    def test_ordinary_input_is_sorted(self) -> None:
        self.assertEqual(
            permutations("cba"),
            ["abc", "acb", "bac", "bca", "cab", "cba"],
        )

    def test_repeated_characters_are_distinct(self) -> None:
        self.assertEqual(permutations("aba"), ["aab", "aba", "baa"])

    def test_empty_input(self) -> None:
        self.assertEqual(permutations(""), [""])

    def test_single_character(self) -> None:
        self.assertEqual(permutations("x"), ["x"])

    def test_seven_distinct_characters(self) -> None:
        text = "gfedcba"
        result = permutations(text)
        self.assertEqual(len(result), math.factorial(7))
        self.assertEqual(result, sorted(set(result)))
        self.assertEqual(result[0], "abcdefg")
        self.assertEqual(result[-1], "gfedcba")
        self.assertTrue(all(sorted(item) == sorted(text) for item in result))
        self.assertEqual(text, "gfedcba")

    def test_seven_identical_characters(self) -> None:
        self.assertEqual(permutations("aaaaaaa"), ["aaaaaaa"])

    def test_character_order_includes_case_and_punctuation(self) -> None:
        self.assertEqual(
            permutations("aA!"),
            ["!Aa", "!aA", "A!a", "Aa!", "a!A", "aA!"],
        )


if __name__ == "__main__":
    unittest.main()
