import unittest
from unittest.mock import patch

from solution import pairs, pairs_legacy


class PairsTests(unittest.TestCase):
    def test_both_public_functions_delegate_to_the_shared_helper(self):
        for function in (pairs, pairs_legacy):
            with self.subTest(function=function.__name__):
                items = [1, 2, 3]
                expected = [(1, 2), (2, 3)]
                with patch("solution._adjacent_pairs", return_value=expected) as helper:
                    self.assertIs(function(items), expected)
                    helper.assert_called_once_with(items)
                    self.assertIs(helper.call_args.args[0], items)

    def test_overlapping_pairs_in_input_order(self):
        for function in (pairs, pairs_legacy):
            with self.subTest(function=function.__name__):
                result = function([1, 2, 3, 2])
                self.assertIsInstance(result, list)
                self.assertEqual(result, [(1, 2), (2, 3), (3, 2)])
                self.assertTrue(all(isinstance(pair, tuple) for pair in result))

    def test_fewer_than_two_items(self):
        for function in (pairs, pairs_legacy):
            for items in ([], [1]):
                with self.subTest(function=function.__name__, items=items):
                    self.assertEqual(function(items), [])

    def test_input_is_unchanged(self):
        for function in (pairs, pairs_legacy):
            with self.subTest(function=function.__name__):
                items = [3, 1, 2, 1]
                original = items.copy()
                function(items)
                self.assertEqual(items, original)

    def test_compatible_sequence_inputs(self):
        for function in (pairs, pairs_legacy):
            with self.subTest(function=function.__name__):
                self.assertEqual(function((1, 2, 3)), [(1, 2), (2, 3)])
                self.assertEqual(function("abc"), [("a", "b"), ("b", "c")])

    def test_invalid_inputs_raise_type_error(self):
        for function in (pairs, pairs_legacy):
            for items in (None, 1, {1, 2}):
                with self.subTest(function=function.__name__, items=items):
                    with self.assertRaises(TypeError):
                        function(items)


if __name__ == "__main__":
    unittest.main()
