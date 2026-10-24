import unittest

from solution import prefix, prefix_legacy


class PrefixTests(unittest.TestCase):
    def test_inclusive_sums_and_input_immutability(self) -> None:
        for function in (prefix, prefix_legacy):
            for items, expected in (
                ([1, 2, 3], [1, 3, 6]),
                ([-2, 5, -4, 0], [-2, 3, -1, -1]),
                ([7], [7]),
                ([], []),
            ):
                with self.subTest(function=function.__name__, items=items):
                    original = items.copy()
                    result = function(items)
                    self.assertEqual(result, expected)
                    self.assertIsInstance(result, list)
                    self.assertEqual(len(result), len(items))
                    self.assertIsNot(result, items)
                    self.assertEqual(items, original)


class PrefixErrorTests(unittest.TestCase):
    def test_invalid_inputs_raise_type_error_without_mutation(self) -> None:
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
