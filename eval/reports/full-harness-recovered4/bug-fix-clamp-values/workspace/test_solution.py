import unittest

from solution import clamp


class ClampTests(unittest.TestCase):
    def test_clamps_to_inclusive_range(self) -> None:
        for value, expected in [(-5, -2), (-2, -2), (0, 0), (3, 3), (8, 3)]:
            with self.subTest(value=value):
                self.assertEqual(clamp(value, -2, 3), expected)

    def test_equal_bounds_are_valid(self) -> None:
        for value in (-5, 2, 8):
            with self.subTest(value=value):
                self.assertEqual(clamp(value, 2, 2), 2)

    def test_reversed_bounds_raise_value_error(self) -> None:
        with self.assertRaises(ValueError):
            clamp(0, 3, -2)


if __name__ == "__main__":
    unittest.main()
