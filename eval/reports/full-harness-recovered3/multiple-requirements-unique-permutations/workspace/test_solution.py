import unittest

from solution import permutations


class PermutationsTests(unittest.TestCase):
    def test_distinct_characters_are_sorted(self):
        self.assertEqual(
            permutations("cba"), ["abc", "acb", "bac", "bca", "cab", "cba"]
        )

    def test_repeated_characters_are_deduplicated(self):
        self.assertEqual(permutations("aba"), ["aab", "aba", "baa"])
        self.assertEqual(permutations("aaaa"), ["aaaa"])

    def test_empty_string_has_one_permutation(self):
        self.assertEqual(permutations(""), [""])

    def test_single_character(self):
        self.assertEqual(permutations("x"), ["x"])

    def test_input_values_and_collection_order_are_preserved(self):
        inputs = ["ba", "aba", ""]
        original = inputs.copy()
        results = [permutations(text) for text in inputs]
        self.assertEqual(inputs, original)
        self.assertEqual(results, [["ab", "ba"], ["aab", "aba", "baa"], [""]])

    def test_lexicographic_order_for_mixed_characters(self):
        self.assertEqual(permutations("aA!"), ["!Aa", "!aA", "A!a", "Aa!", "a!A", "aA!"])

    def test_seven_distinct_characters(self):
        result = permutations("gfedcba")
        self.assertEqual(len(result), 5040)
        self.assertEqual(len(set(result)), 5040)
        self.assertEqual(result, sorted(result))
        self.assertEqual(result[0], "abcdefg")
        self.assertEqual(result[-1], "gfedcba")
        self.assertTrue(all(sorted(value) == list("abcdefg") for value in result))


if __name__ == "__main__":
    unittest.main()
