"""Tests for the public permutations API."""

import math
import unittest

from solution import permutations


class PermutationsTests(unittest.TestCase):
    def test_ordinary_strings(self) -> None:
        expected = ["abc", "acb", "bac", "bca", "cab", "cba"]
        for text in ("abc", "cba", "bac"):
            with self.subTest(text=text):
                self.assertEqual(permutations(text), expected)

    def test_repeated_characters(self) -> None:
        for text in ("aab", "aba", "baa"):
            with self.subTest(text=text):
                self.assertEqual(permutations(text), ["aab", "aba", "baa"])

    def test_empty_string(self) -> None:
        self.assertEqual(permutations(""), [""])

    def test_single_character(self) -> None:
        for text in ("a", "!", "é"):
            with self.subTest(text=text):
                self.assertEqual(permutations(text), [text])

    def test_character_order(self) -> None:
        self.assertEqual(permutations("aA"), ["Aa", "aA"])
        self.assertEqual(permutations("éaé"), ["aéé", "éaé", "ééa"])
        self.assertEqual(permutations("a "), [" a", "a "])

    def test_seven_repeated_characters(self) -> None:
        self.assertEqual(permutations("aaaaaaa"), ["aaaaaaa"])
        self.assertEqual(
            permutations("baaaaaa"),
            ["aaaaaab", "aaaaaba", "aaaabaa", "aaabaaa", "aabaaaa", "abaaaaa", "baaaaaa"],
        )

    def test_seven_distinct_characters(self) -> None:
        result = permutations("gfedcba")

        self.assertEqual(len(result), math.factorial(7))
        self.assertEqual(result, sorted(set(result)))
        self.assertEqual(result[0], "abcdefg")
        self.assertEqual(result[-1], "gfedcba")
        self.assertTrue(all(sorted(item) == list("abcdefg") for item in result))


if __name__ == "__main__":
    unittest.main()
