import unittest

from solution import clamp


class ClampTests(unittest.TestCase):
    def test_values_below_within_and_above_range(self):
        for value, expected in [(-10, -3), (-1, -1), (10, 4)]:
            with self.subTest(value=value):
                self.assertEqual(clamp(value, -3, 4), expected)

    def test_inclusive_endpoints(self):
        self.assertEqual(clamp(-3, -3, 4), -3)
        self.assertEqual(clamp(4, -3, 4), 4)

    def test_equal_bounds(self):
        for value in (-100, 5, 100):
            with self.subTest(value=value):
                self.assertEqual(clamp(value, 5, 5), 5)

    def test_reversed_bounds_raise_value_error(self):
        for value in (-100, 5, 100):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    clamp(value, 10, 0)

    def test_preserves_input_values_and_collection_order(self):
        values = [8, -5, 2, 8, 0]
        original = values.copy()
        results = [clamp(value, 0, 6) for value in values]
        self.assertEqual(results, [6, 0, 2, 6, 0])
        self.assertEqual(values, original)

    def test_in_range_value_is_returned_unchanged(self):
        value = int("1000000")
        self.assertIs(clamp(value, 0, 2000000), value)


if __name__ == "__main__":
    unittest.main()
