import unittest

from solution import prefix, prefix_legacy


class PrefixTests(unittest.TestCase):
    def test_inclusive_sums_preserve_length_and_input(self) -> None:
        for function in (prefix, prefix_legacy):
            for items, expected in (
                ([1, 2, 3], [1, 3, 6]),
                ([-2, 5, -4, 0], [-2, 3, -1, -1]),
                ([7], [7]),
            ):
                with self.subTest(function=function.__name__, items=items):
                    original = items.copy()
                    result = function(items)
                    self.assertEqual(result, expected)
                    self.assertIsInstance(result, list)
                    self.assertEqual(len(result), len(items))
                    self.assertEqual(items, original)
                    self.assertIsNot(result, items)

    def test_empty_input_returns_fresh_list(self) -> None:
        for function in (prefix, prefix_legacy):
            with self.subTest(function=function.__name__):
                items: list[int] = []
                result = function(items)
                self.assertEqual(result, [])
                self.assertIsNot(result, items)
                self.assertIsNot(result, function(items))
                self.assertEqual(items, [])

    def test_invalid_inputs_keep_type_error_behavior(self) -> None:
        for function in (prefix, prefix_legacy):
            with self.subTest(function=function.__name__, case="not iterable"):
                with self.assertRaises(TypeError):
                    function(None)  # type: ignore[arg-type]
            with self.subTest(function=function.__name__, case="invalid item"):
                items = [1, "invalid", 3]
                original = items.copy()
                with self.assertRaises(TypeError):
                    function(items)  # type: ignore[arg-type]
                self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
