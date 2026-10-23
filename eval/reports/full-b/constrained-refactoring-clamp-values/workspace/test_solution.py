import inspect
import unittest

from solution import clamp, clamp_legacy


class ClampTests(unittest.TestCase):
    def test_clamps_values_to_inclusive_bounds(self) -> None:
        for function in (clamp, clamp_legacy):
            for value, low, high, expected in (
                (-5, 0, 10, 0),
                (0, 0, 10, 0),
                (5, 0, 10, 5),
                (10, 0, 10, 10),
                (15, 0, 10, 10),
                (-15, -10, -2, -10),
                (-5, -10, -2, -5),
                (0, -10, -2, -2),
            ):
                with self.subTest(function=function.__name__, value=value, low=low, high=high):
                    result = function(value, low, high)
                    self.assertEqual(result, expected)
                    self.assertIs(type(result), int)

    def test_equal_bounds_are_valid(self) -> None:
        for function in (clamp, clamp_legacy):
            for value in (-10, 3, 10):
                with self.subTest(function=function.__name__, value=value):
                    self.assertEqual(function(value, 3, 3), 3)

    def test_reversed_bounds_preserve_error(self) -> None:
        for function in (clamp, clamp_legacy):
            for value in (-10, 3, 10):
                with self.subTest(function=function.__name__, value=value):
                    with self.assertRaises(ValueError) as raised:
                        function(value, 5, 2)
                    self.assertEqual(raised.exception.args, ("reversed bounds",))

    def test_collection_inputs_remain_unchanged(self) -> None:
        for function in (clamp, clamp_legacy):
            for number in (-1, 0, 5, 10, 11):
                with self.subTest(function=function.__name__, value=number):
                    value, low, high = [number], [0], [10]
                    snapshots = (value.copy(), low.copy(), high.copy())
                    expected = low if number <= 0 else high if number > 10 else value

                    result = function(value, low, high)

                    self.assertIs(result, expected)
                    self.assertEqual((value, low, high), snapshots)

    def test_reversed_collection_bounds_remain_unchanged(self) -> None:
        for function in (clamp, clamp_legacy):
            with self.subTest(function=function.__name__):
                value, low, high = [3], [5], [2]
                snapshots = (value.copy(), low.copy(), high.copy())

                with self.assertRaises(ValueError):
                    function(value, low, high)

                self.assertEqual((value, low, high), snapshots)

    def test_public_signatures_and_keyword_arguments(self) -> None:
        for function in (clamp, clamp_legacy):
            with self.subTest(function=function.__name__):
                signature = inspect.signature(function)
                self.assertEqual(list(signature.parameters), ["value", "low", "high"])
                self.assertEqual(signature.return_annotation, int)
                for parameter in signature.parameters.values():
                    self.assertEqual(parameter.kind, inspect.Parameter.POSITIONAL_OR_KEYWORD)
                    self.assertIs(parameter.default, inspect.Parameter.empty)
                    self.assertEqual(parameter.annotation, int)
                self.assertEqual(function(value=7, low=0, high=5), 5)


if __name__ == "__main__":
    unittest.main()
