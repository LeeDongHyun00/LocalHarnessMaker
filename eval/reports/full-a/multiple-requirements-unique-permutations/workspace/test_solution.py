import unittest

from solution import permutations


class PermutationsTests(unittest.TestCase):
    def test_distinct_characters_are_sorted(self) -> None:
        self.assertEqual(
            permutations("cba"), ["abc", "acb", "bac", "bca", "cab", "cba"]
        )

    def test_duplicate_characters_produce_distinct_results(self) -> None:
        self.assertEqual(permutations("aba"), ["aab", "aba", "baa"])
        self.assertEqual(permutations("aaaaaaa"), ["aaaaaaa"])

    def test_empty_and_single_character(self) -> None:
        self.assertEqual(permutations(""), [""])
        self.assertEqual(permutations("x"), ["x"])

    def test_input_values_and_collection_order_are_preserved(self) -> None:
        inputs = ["ba", "", "aba", "ba"]
        original = inputs.copy()
        results = [permutations(text) for text in inputs]
        self.assertEqual(inputs, original)
        self.assertEqual(
            results,
            [["ab", "ba"], [""], ["aab", "aba", "baa"], ["ab", "ba"]],
        )

    def test_lexicographic_order_preserves_case_and_unicode(self) -> None:
        self.assertEqual(permutations("éaA"), ["Aaé", "Aéa", "aAé", "aéA", "éAa", "éaA"])

    def test_seven_distinct_characters(self) -> None:
        result = permutations("gfedcba")
        self.assertEqual(len(result), 5040)
        self.assertEqual(len(set(result)), 5040)
        self.assertEqual(result, sorted(result))
        self.assertEqual(result[0], "abcdefg")
        self.assertEqual(result[-1], "gfedcba")
        self.assertTrue(all(sorted(value) == list("abcdefg") for value in result))


if __name__ == "__main__":
    unittest.main()
