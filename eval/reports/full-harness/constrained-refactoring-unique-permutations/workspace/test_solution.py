import unittest

from solution import permutations, permutations_legacy


class PermutationsTests(unittest.TestCase):
    def test_distinct_sorted_permutations(self):
        for function in (permutations, permutations_legacy):
            with self.subTest(function=function.__name__):
                result = function('baa')
                self.assertIsInstance(result, list)
                self.assertEqual(result, ['aab', 'aba', 'baa'])
                self.assertEqual(function('cba'),
                                 ['abc', 'acb', 'bac', 'bca', 'cab', 'cba'])

    def test_empty_and_single_character(self):
        for function in (permutations, permutations_legacy):
            with self.subTest(function=function.__name__):
                self.assertEqual(function(''), [''])
                self.assertEqual(function('x'), ['x'])

    def test_input_collections_are_unchanged(self):
        for function in (permutations, permutations_legacy):
            with self.subTest(function=function.__name__):
                characters = ['b', 'a', 'a']
                self.assertEqual(function(characters), ['aab', 'aba', 'baa'])
                self.assertEqual(characters, ['b', 'a', 'a'])

    def test_invalid_inputs_raise_type_error(self):
        for function in (permutations, permutations_legacy):
            for value in (None, 123, ['a', 1]):
                with self.subTest(function=function.__name__, value=value):
                    with self.assertRaises(TypeError):
                        function(value)


if __name__ == '__main__':
    unittest.main()
