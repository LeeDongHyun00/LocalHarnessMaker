import unittest

from solution import clamp


class ClampTests(unittest.TestCase):
    def test_values_within_inclusive_bounds_are_preserved(self) -> None:
        for value in (-5, 0, 5):
            with self.subTest(value=value):
                self.assertEqual(clamp(value, -5, 5), value)

    def test_values_outside_bounds_are_clamped(self) -> None:
        self.assertEqual(clamp(-10, -5, 5), -5)
        self.assertEqual(clamp(10, -5, 5), 5)
        self.assertEqual(clamp(-1, 2, 7), 2)
        self.assertEqual(clamp(0, -7, -2), -2)

    def test_equal_bounds_are_valid(self) -> None:
        for value in (-10, 3, 10):
            with self.subTest(value=value):
                self.assertEqual(clamp(value, 3, 3), 3)

    def test_reversed_bounds_raise_value_error(self) -> None:
        for value in (-10, 0, 10):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    clamp(value, 5, -5)

    def test_clamping_collection_preserves_inputs_and_order(self) -> None:
        values = [8, -4, 2, 8, 0, -1]
        original = values.copy()

        results = [clamp(value, 0, 5) for value in values]

        self.assertEqual(results, [5, 0, 2, 5, 0, 0])
        self.assertEqual(values, original)


if __name__ == "__main__":
    unittest.main()
