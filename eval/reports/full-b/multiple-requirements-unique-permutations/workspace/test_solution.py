import unittest

from solution import permutations


class PermutationsTests(unittest.TestCase):
    def test_distinct_characters_are_sorted(self) -> None:
        self.assertEqual(
            permutations("cba"),
            ["abc", "acb", "bac", "bca", "cab", "cba"],
        )

    def test_repeated_characters_produce_distinct_results(self) -> None:
        self.assertEqual(permutations("aba"), ["aab", "aba", "baa"])
        self.assertEqual(
            permutations("bbaa"),
            ["aabb", "abab", "abba", "baab", "baba", "bbaa"],
        )

    def test_empty_string_has_one_permutation(self) -> None:
        self.assertEqual(permutations(""), [""])

    def test_single_and_identical_characters(self) -> None:
        self.assertEqual(permutations("x"), ["x"])
        self.assertEqual(permutations("aaaaaaa"), ["aaaaaaa"])

    def test_lexicographic_order_includes_case_and_unicode(self) -> None:
        self.assertEqual(
            permutations("éaA"),
            ["Aaé", "Aéa", "aAé", "aéA", "éAa", "éaA"],
        )

    def test_seven_distinct_characters(self) -> None:
        result = permutations("gfedcba")
        self.assertEqual(len(result), 5040)
        self.assertEqual(len(set(result)), 5040)
        self.assertEqual(result, sorted(result))
        self.assertEqual(result[0], "abcdefg")
        self.assertEqual(result[-1], "gfedcba")
        self.assertTrue(all(sorted(item) == list("abcdefg") for item in result))

    def test_input_values_and_collection_order_are_preserved(self) -> None:
        inputs = ["ba", "", "aba", "ba"]
        original = inputs.copy()

        results = [permutations(text) for text in inputs]

        self.assertEqual(inputs, original)
        self.assertEqual(
            results,
            [["ab", "ba"], [""], ["aab", "aba", "baa"], ["ab", "ba"]],
        )


if __name__ == "__main__":
    unittest.main()
