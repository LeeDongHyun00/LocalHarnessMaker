import unittest

from solution import permutations, permutations_legacy


class PermutationsTests(unittest.TestCase):
    def test_distinct_permutations_are_sorted(self) -> None:
        for function in (permutations, permutations_legacy):
            with self.subTest(function=function.__name__):
                result = function('baa')
                self.assertIsInstance(result, list)
                self.assertEqual(result, ['aab', 'aba', 'baa'])
                self.assertEqual(function('ba'), ['ab', 'ba'])

    def test_empty_and_single_character_inputs(self) -> None:
        for function in (permutations, permutations_legacy):
            with self.subTest(function=function.__name__):
                self.assertEqual(function(''), [''])
                self.assertEqual(function('x'), ['x'])

    def test_input_collections_remain_unchanged(self) -> None:
        for function in (permutations, permutations_legacy):
            with self.subTest(function=function.__name__):
                characters = ['b', 'a', 'a']
                self.assertEqual(function(characters), ['aab', 'aba', 'baa'])
                self.assertEqual(characters, ['b', 'a', 'a'])

    def test_invalid_inputs_raise_type_error(self) -> None:
        for function in (permutations, permutations_legacy):
            for value in (None, 42, ['a', 1]):
                with self.subTest(function=function.__name__, value=value):
                    with self.assertRaises(TypeError):
                        function(value)


if __name__ == '__main__':
    unittest.main()
