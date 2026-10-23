import unittest

from solution import permutations


class PermutationsTests(unittest.TestCase):
    def test_distinct_permutations_in_lexicographic_order(self) -> None:
        self.assertEqual(permutations("baa"), ["aab", "aba", "baa"])

    def test_empty_string(self) -> None:
        self.assertEqual(permutations(""), [""])

    def test_all_distinct_characters(self) -> None:
        self.assertEqual(
            permutations("cba"), ["abc", "acb", "bac", "bca", "cab", "cba"]
        )


if __name__ == "__main__":
    unittest.main()
