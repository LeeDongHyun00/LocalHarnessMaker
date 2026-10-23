import unittest

from solution import permutations


class PermutationsTests(unittest.TestCase):
    def test_distinct_sorted_permutations(self) -> None:
        self.assertEqual(permutations("aba"), ["aab", "aba", "baa"])
        self.assertEqual(
            permutations("cba"), ["abc", "acb", "bac", "bca", "cab", "cba"]
        )

    def test_empty_and_single_character(self) -> None:
        self.assertEqual(permutations(""), [""])
        self.assertEqual(permutations("a"), ["a"])
        self.assertEqual(permutations("aaa"), ["aaa"])


if __name__ == "__main__":
    unittest.main()
