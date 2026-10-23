import unittest

from solution import pairs, pairs_legacy


class PairsTests(unittest.TestCase):
    def test_overlapping_pairs_preserve_order_and_input(self):
        for function in (pairs, pairs_legacy):
            with self.subTest(function=function.__name__):
                items = [3, 1, 1, 2]
                result = function(items)
                self.assertEqual(result, [(3, 1), (1, 1), (1, 2)])
                self.assertIsInstance(result, list)
                self.assertTrue(all(isinstance(pair, tuple) for pair in result))
                self.assertEqual(items, [3, 1, 1, 2])

    def test_short_inputs_return_empty_lists(self):
        for function in (pairs, pairs_legacy):
            for items in ([], [1]):
                with self.subTest(function=function.__name__, items=items):
                    original = items.copy()
                    self.assertEqual(function(items), [])
                    self.assertEqual(items, original)

    def test_existing_sliceable_inputs_remain_supported(self):
        for function in (pairs, pairs_legacy):
            for items in ((1, 2, 3), "abc"):
                with self.subTest(function=function.__name__, items=items):
                    self.assertEqual(function(items), list(zip(items, items[1:])))

    def test_unsupported_inputs_keep_type_errors(self):
        for function in (pairs, pairs_legacy):
            for items in (None, 1, {1, 2}, iter([1, 2])):
                with self.subTest(function=function.__name__, items=items):
                    with self.assertRaises(TypeError):
                        function(items)


if __name__ == "__main__":
    unittest.main()
