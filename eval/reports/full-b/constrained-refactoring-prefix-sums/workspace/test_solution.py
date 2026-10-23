import unittest

from solution import prefix, prefix_legacy


class PrefixTests(unittest.TestCase):
    def test_inclusive_prefix_sums(self) -> None:
        cases = [
            ([1, 2, 3, 4], [1, 3, 6, 10]),
            ([-2, 3, -4, 0, 5], [-2, 1, -3, -3, 2]),
            ([0, 0], [0, 0]),
            ([7], [7]),
        ]
        for function in (prefix, prefix_legacy):
            for items, expected in cases:
                with self.subTest(function=function.__name__, items=items):
                    result = function(items)
                    self.assertIs(type(result), list)
                    self.assertEqual(result, expected)
                    self.assertEqual(len(result), len(items))

    def test_empty_input_returns_fresh_list(self) -> None:
        for function in (prefix, prefix_legacy):
            with self.subTest(function=function.__name__):
                items = []
                result = function(items)
                self.assertIs(type(result), list)
                self.assertEqual(result, [])
                self.assertIsNot(result, items)
                self.assertIsNot(result, function(items))

    def test_input_is_not_mutated(self) -> None:
        for function in (prefix, prefix_legacy):
            with self.subTest(function=function.__name__):
                items = [3, -1, 2]
                original = items.copy()
                result = function(items)
                self.assertEqual(items, original)
                self.assertIsNot(result, items)
                result.append(99)
                self.assertEqual(items, original)

    def test_invalid_inputs_raise_without_mutation(self) -> None:
        for function in (prefix, prefix_legacy):
            with self.subTest(function=function.__name__):
                with self.assertRaises(TypeError):
                    function(None)
                items = [1, "invalid", 3]
                original = items.copy()
                with self.assertRaises(TypeError):
                    function(items)
                self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
