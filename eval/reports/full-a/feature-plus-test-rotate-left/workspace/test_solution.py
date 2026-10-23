"""Tests for the public rotate API."""

import unittest

from solution import rotate


class RotateTests(unittest.TestCase):
    def test_ordinary_rotations(self) -> None:
        self.assertEqual(rotate([1, 2, 3], 1), [2, 3, 1])
        self.assertEqual(rotate([1, 2, 3], -1), [3, 1, 2])
        self.assertEqual(rotate([1, 2, 3, 4], 2), [3, 4, 1, 2])

    def test_boundary_steps(self) -> None:
        for steps, expected in (
            (0, [1, 2, 3]),
            (3, [1, 2, 3]),
            (-3, [1, 2, 3]),
            (4, [2, 3, 1]),
            (-4, [3, 1, 2]),
            (10**30, [2, 3, 1]),
            (-(10**30), [3, 1, 2]),
        ):
            with self.subTest(steps=steps):
                self.assertEqual(rotate([1, 2, 3], steps), expected)

    def test_empty_and_singleton_inputs(self) -> None:
        for steps in (0, 1, -1, 100):
            with self.subTest(steps=steps):
                self.assertEqual(rotate([], steps), [])
                self.assertEqual(rotate([7], steps), [7])

    def test_input_is_unchanged_and_result_is_new(self) -> None:
        for items in ([], [1], [1, 2, 3]):
            for steps in (0, 1, -1, 3):
                with self.subTest(items=items, steps=steps):
                    original = items.copy()
                    result = rotate(items, steps)
                    self.assertEqual(items, original)
                    self.assertIsNot(result, items)
                    result.append(99)
                    self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
