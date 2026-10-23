import unittest
from itertools import permutations as permute

from solution import permutations, permutations_legacy


class PermutationsTests(unittest.TestCase):
    def test_distinct_sorted_permutations(self) -> None:
        for function in (permutations, permutations_legacy):
            for text, expected in (
                ("baa", ["aab", "aba", "baa"]),
                ("ba", ["ab", "ba"]),
                ("aaa", ["aaa"]),
                ("éA", ["Aé", "éA"]),
                ("aaaaaab", sorted("a" * i + "b" + "a" * (6 - i)
                                   for i in range(7))),
            ):
                with self.subTest(function=function.__name__, text=text):
                    result = function(text)
                    self.assertIs(type(result), list)
                    self.assertEqual(result, expected)

    def test_empty_and_single_character(self) -> None:
        for function in (permutations, permutations_legacy):
            with self.subTest(function=function.__name__):
                self.assertEqual(function(""), [""])
                self.assertEqual(function("x"), ["x"])

    def test_input_collections_are_unchanged(self) -> None:
        for function in (permutations, permutations_legacy):
            for characters in (["b", "a", "a"], ("b", "a", "a")):
                with self.subTest(function=function.__name__, characters=characters):
                    before = characters[:]
                    self.assertEqual(function(characters), ["aab", "aba", "baa"])
                    self.assertEqual(characters, before)

    def test_original_error_behavior(self) -> None:
        for function in (permutations, permutations_legacy):
            for value in (None, 123, [1], ["a", 1], [["a"]], b"ab"):
                with self.subTest(function=function.__name__, value=value):
                    # The original implementation establishes both exception type
                    # and message for inputs outside the annotated string API.
                    with self.assertRaises(TypeError) as original:
                        sorted({"".join(p) for p in permute(value)})
                    with self.assertRaises(type(original.exception)) as current:
                        function(value)
                    self.assertEqual(str(current.exception), str(original.exception))


if __name__ == "__main__":
    unittest.main()
