import unittest

from solution import clamp


class ClampTests(unittest.TestCase):
    def test_clamp_inclusive_range(self) -> None:
        for value, expected in [(-1, 0), (0, 0), (5, 5), (10, 10), (11, 10)]:
            with self.subTest(value=value):
                self.assertEqual(clamp(value, 0, 10), expected)

    def test_equal_bounds(self) -> None:
        for value in (2, 3, 4):
            with self.subTest(value=value):
                self.assertEqual(clamp(value, 3, 3), 3)

    def test_reversed_bounds_raise(self) -> None:
        with self.assertRaises(ValueError):
            clamp(5, 10, 0)


if __name__ == "__main__":
    unittest.main()
