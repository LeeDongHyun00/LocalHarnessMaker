import unittest

from solution import pairs, pairs_legacy


class PairsTests(unittest.TestCase):
    def test_adjacent_pairs_in_input_order(self):
        cases = [
            ([], []),
            ([1], []),
            ([1, 2], [(1, 2)]),
            ([1, 2, 3], [(1, 2), (2, 3)]),
            ([3, -1, 3, 3], [(3, -1), (-1, 3), (3, 3)]),
        ]
        for function in (pairs, pairs_legacy):
            for items, expected in cases:
                with self.subTest(function=function.__name__, items=items):
                    result = function(items)
                    self.assertEqual(result, expected)
                    self.assertIsInstance(result, list)
                    for pair in result:
                        self.assertIsInstance(pair, tuple)

    def test_input_list_is_unchanged(self):
        for function in (pairs, pairs_legacy):
            with self.subTest(function=function.__name__):
                items = [3, 1, 3, 2]
                original = items.copy()
                function(items)
                self.assertEqual(items, original)

    def test_existing_sequence_compatibility(self):
        cases = [
            ((1, 2, 3), [(1, 2), (2, 3)]),
            (range(3), [(0, 1), (1, 2)]),
            ("abc", [("a", "b"), ("b", "c")]),
        ]
        for function in (pairs, pairs_legacy):
            for items, expected in cases:
                with self.subTest(function=function.__name__, items=items):
                    self.assertEqual(function(items), expected)

    def test_non_subscriptable_inputs_raise_type_error(self):
        for function in (pairs, pairs_legacy):
            for items in (None, 42, {1, 2, 3}, iter([1, 2, 3])):
                with self.subTest(function=function.__name__, items=items):
                    with self.assertRaisesRegex(TypeError, "object is not subscriptable"):
                        function(items)


if __name__ == "__main__":
    unittest.main()
