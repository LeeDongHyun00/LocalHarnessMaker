import unittest

from solution import permutations


class PermutationsTests(unittest.TestCase):
    def test_distinct_permutations_in_sorted_order(self) -> None:
        self.assertEqual(permutations("baa"), ["aab", "aba", "baa"])

    def test_all_permutations(self) -> None:
        self.assertEqual(
            permutations("cba"), ["abc", "acb", "bac", "bca", "cab", "cba"]
        )

    def test_empty_string(self) -> None:
        self.assertEqual(permutations(""), [""])


if __name__ == "__main__":
    unittest.main()
