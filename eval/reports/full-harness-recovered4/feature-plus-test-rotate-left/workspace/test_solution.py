"""Public tests for list rotation."""

import unittest

from solution import rotate


class RotateTests(unittest.TestCase):
    def test_ordinary_rotations(self) -> None:
        for steps, expected in (
            (1, [2, 3, 1]),
            (2, [3, 1, 2]),
            (4, [2, 3, 1]),
            (-1, [3, 1, 2]),
            (-4, [3, 1, 2]),
        ):
            with self.subTest(steps=steps):
                items = [1, 2, 3]
                self.assertEqual(rotate(items, steps), expected)
                self.assertEqual(items, [1, 2, 3])

    def test_boundary_rotations_return_new_lists(self) -> None:
        for items, steps in (
            ([1, 2, 3], 0),
            ([1, 2, 3], 3),
            ([1, 2, 3], -6),
            ([7], 100),
            ([7], -100),
        ):
            with self.subTest(items=items, steps=steps):
                original = items.copy()
                result = rotate(items, steps)
                self.assertEqual(result, original)
                self.assertEqual(items, original)
                self.assertIsNot(result, items)

    def test_empty_input(self) -> None:
        for steps in (0, 1, -1, 100):
            with self.subTest(steps=steps):
                items: list[int] = []
                result = rotate(items, steps)
                self.assertEqual(result, [])
                self.assertEqual(items, [])
                self.assertIsNot(result, items)


if __name__ == "__main__":
    unittest.main()
