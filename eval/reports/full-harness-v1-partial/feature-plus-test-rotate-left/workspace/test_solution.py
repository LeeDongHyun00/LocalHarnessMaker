"""Tests for the public rotate API."""

import unittest

from solution import rotate


class RotateTests(unittest.TestCase):
    def test_ordinary_rotations(self):
        self.assertEqual(rotate([1, 2, 3, 4], 1), [2, 3, 4, 1])
        self.assertEqual(rotate([1, 2, 3, 4], 2), [3, 4, 1, 2])
        self.assertEqual(rotate([1, 2, 3, 4], -1), [4, 1, 2, 3])

    def test_boundary_and_wrapped_steps(self):
        for steps, expected in [
            (0, [1, 2, 3]),
            (3, [1, 2, 3]),
            (-3, [1, 2, 3]),
            (4, [2, 3, 1]),
            (-4, [3, 1, 2]),
            (10**100, [2, 3, 1]),
            (-(10**100), [3, 1, 2]),
        ]:
            with self.subTest(steps=steps):
                self.assertEqual(rotate([1, 2, 3], steps), expected)

    def test_empty_and_single_item(self):
        for steps in (0, 1, -1, 100):
            with self.subTest(steps=steps):
                self.assertEqual(rotate([], steps), [])
                self.assertEqual(rotate([7], steps), [7])

    def test_input_is_unchanged_and_result_is_new(self):
        for original in ([], [7], [1, 2, 3]):
            for steps in (0, 1, -1, 3):
                with self.subTest(items=original, steps=steps):
                    items = original.copy()
                    result = rotate(items, steps)
                    self.assertEqual(items, original)
                    self.assertIsNot(result, items)
                    result.append(99)
                    self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
