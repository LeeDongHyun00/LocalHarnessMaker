import unittest

from solution import permutations


class PermutationsTests(unittest.TestCase):
    def test_distinct_permutations_are_sorted(self) -> None:
        self.assertEqual(permutations("baa"), ["aab", "aba", "baa"])

    def test_empty_string_has_one_permutation(self) -> None:
        self.assertEqual(permutations(""), [""])


if __name__ == "__main__":
    unittest.main()
