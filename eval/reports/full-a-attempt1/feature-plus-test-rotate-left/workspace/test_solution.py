"""Tests for the public rotate API."""

import unittest

from solution import rotate


class RotateTests(unittest.TestCase):
    def test_ordinary_rotations(self) -> None:
        for steps, expected in (
            (1, [2, 3, 4, 1]),
            (2, [3, 4, 1, 2]),
            (-1, [4, 1, 2, 3]),
            (-2, [3, 4, 1, 2]),
        ):
            with self.subTest(steps=steps):
                self.assertEqual(rotate([1, 2, 3, 4], steps), expected)

    def test_modulo_and_boundary_steps(self) -> None:
        for steps, expected in (
            (0, [1, 2, 3]),
            (3, [1, 2, 3]),
            (-3, [1, 2, 3]),
            (4, [2, 3, 1]),
            (-4, [3, 1, 2]),
            (10**100, [2, 3, 1]),
            (-(10**100), [3, 1, 2]),
        ):
            with self.subTest(steps=steps):
                self.assertEqual(rotate([1, 2, 3], steps), expected)

    def test_empty_input(self) -> None:
        for steps in (0, 1, -1, 10**100):
            with self.subTest(steps=steps):
                items: list[int] = []
                result = rotate(items, steps)
                self.assertEqual(result, [])
                self.assertIsNot(result, items)

    def test_single_item(self) -> None:
        for steps in (0, 1, -1, 100):
            with self.subTest(steps=steps):
                self.assertEqual(rotate([7], steps), [7])

    def test_input_is_unchanged_and_result_is_new(self) -> None:
        for steps in (0, 1, -1, 3):
            with self.subTest(steps=steps):
                items = [1, 2, 3]
                result = rotate(items, steps)
                self.assertEqual(items, [1, 2, 3])
                self.assertIsNot(result, items)
                result.append(4)
                self.assertEqual(items, [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
