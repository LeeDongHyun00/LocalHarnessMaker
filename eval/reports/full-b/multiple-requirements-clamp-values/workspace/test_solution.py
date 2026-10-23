import unittest

from solution import clamp


class ClampTests(unittest.TestCase):
    def test_values_below_low_return_low(self) -> None:
        for value, low, high in [(-1, 0, 10), (-20, -10, -1)]:
            with self.subTest(value=value, low=low, high=high):
                self.assertEqual(clamp(value, low, high), low)

    def test_values_above_high_return_high(self) -> None:
        for value, low, high in [(11, 0, 10), (0, -10, -1)]:
            with self.subTest(value=value, low=low, high=high):
                self.assertEqual(clamp(value, low, high), high)

    def test_values_including_boundaries_are_preserved(self) -> None:
        for value in (-5, -2, 0, 3, 5):
            with self.subTest(value=value):
                self.assertEqual(clamp(value, -5, 5), value)

    def test_equal_bounds_are_valid(self) -> None:
        for bound in (-3, 0, 4):
            for value in (bound - 1, bound, bound + 1):
                with self.subTest(value=value, bound=bound):
                    self.assertEqual(clamp(value, bound, bound), bound)

    def test_reversed_bounds_raise_value_error(self) -> None:
        for low, high in [(10, 0), (-1, -10)]:
            for value in (high - 1, high, low, low + 1):
                with self.subTest(value=value, low=low, high=high):
                    with self.assertRaises(ValueError):
                        clamp(value, low, high)

    def test_clamping_collection_preserves_inputs_and_order(self) -> None:
        values = [7, -3, 4, 2, 9, 0, 4]
        original_values = values.copy()

        result = [clamp(value, 0, 5) for value in values]

        self.assertEqual(result, [5, 0, 4, 2, 5, 0, 4])
        self.assertEqual(values, original_values)


if __name__ == "__main__":
    unittest.main()
