import unittest

from solution import permutations, permutations_legacy


class PermutationsTests(unittest.TestCase):
    def test_distinct_permutations_in_lexicographic_order(self) -> None:
        cases = (
            ("bba", ["abb", "bab", "bba"]),
            ("cba", ["abc", "acb", "bac", "bca", "cab", "cba"]),
            ("aaa", ["aaa"]),
            ("éAa", ["Aaé", "Aéa", "aAé", "aéA", "éAa", "éaA"]),
        )
        for function in (permutations, permutations_legacy):
            for text, expected in cases:
                with self.subTest(function=function.__name__, text=text):
                    result = function(text)
                    self.assertIsInstance(result, list)
                    self.assertEqual(result, expected)

    def test_empty_and_single_character_inputs(self) -> None:
        for function in (permutations, permutations_legacy):
            with self.subTest(function=function.__name__):
                self.assertEqual(function(""), [""])
                self.assertEqual(function("x"), ["x"])

    def test_seven_distinct_characters(self) -> None:
        for function in (permutations, permutations_legacy):
            with self.subTest(function=function.__name__):
                result = function("gfedcba")
                self.assertEqual(len(result), 5040)
                self.assertEqual(result, sorted(set(result)))
                self.assertEqual(result[0], "abcdefg")
                self.assertEqual(result[-1], "gfedcba")
                self.assertTrue(all(sorted(item) == list("abcdefg") for item in result))

    def test_input_collection_is_not_mutated(self) -> None:
        for function in (permutations, permutations_legacy):
            with self.subTest(function=function.__name__):
                characters = ["b", "a", "a"]
                original = characters.copy()
                self.assertEqual(function(characters), ["aab", "aba", "baa"])
                self.assertEqual(characters, original)

    def test_non_iterable_inputs_raise_type_error(self) -> None:
        for function in (permutations, permutations_legacy):
            for invalid in (None, 42):
                with self.subTest(function=function.__name__, invalid=invalid):
                    with self.assertRaises(TypeError):
                        function(invalid)

    def test_invalid_character_does_not_mutate_input(self) -> None:
        for function in (permutations, permutations_legacy):
            with self.subTest(function=function.__name__):
                characters = ["a", 1]
                original = characters.copy()
                with self.assertRaises(TypeError):
                    function(characters)
                self.assertEqual(characters, original)


if __name__ == "__main__":
    unittest.main()
