import unittest
from unittest.mock import patch

from solution import permutations, permutations_legacy


class PermutationsTests(unittest.TestCase):
    def test_both_public_functions_delegate_to_shared_helper(self) -> None:
        for function in (permutations, permutations_legacy):
            with self.subTest(function=function.__name__):
                expected = ['ab', 'ba']
                with patch('solution._distinct_permutations', return_value=expected) as helper:
                    self.assertIs(function(text='ba'), expected)
                    helper.assert_called_once_with('ba')

    def test_distinct_permutations_are_sorted_lists(self) -> None:
        for function in (permutations, permutations_legacy):
            for text, expected in (
                ('baa', ['aab', 'aba', 'baa']),
                ('cba', ['abc', 'acb', 'bac', 'bca', 'cab', 'cba']),
                ('aaaaaaa', ['aaaaaaa']),
                ('éa', ['aé', 'éa']),
            ):
                with self.subTest(function=function.__name__, text=text):
                    result = function(text)
                    self.assertIsInstance(result, list)
                    self.assertEqual(result, expected)

    def test_empty_and_single_character(self) -> None:
        for function in (permutations, permutations_legacy):
            with self.subTest(function=function.__name__):
                self.assertEqual(function(''), [''])
                self.assertEqual(function('x'), ['x'])

    def test_existing_iterable_support_preserves_input(self) -> None:
        for function in (permutations, permutations_legacy):
            with self.subTest(function=function.__name__):
                characters = ['b', 'a', 'a']
                self.assertEqual(function(characters), ['aab', 'aba', 'baa'])
                self.assertEqual(characters, ['b', 'a', 'a'])
                self.assertEqual(function(('b', 'a')), ['ab', 'ba'])

    def test_invalid_inputs_keep_type_errors(self) -> None:
        for function in (permutations, permutations_legacy):
            for value in (None, 42, ['a', 1], b'ab'):
                with self.subTest(function=function.__name__, value=value):
                    with self.assertRaises(TypeError):
                        function(value)
            characters = ['a', 1]
            with self.assertRaises(TypeError):
                function(characters)
            self.assertEqual(characters, ['a', 1])


if __name__ == '__main__':
    unittest.main()
