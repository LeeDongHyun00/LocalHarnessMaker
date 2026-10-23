import unittest

from solution import rotate


class RotateTests(unittest.TestCase):
    def test_rotates_left(self) -> None:
        self.assertEqual(rotate([1, 2, 3, 4, 5], 2), [3, 4, 5, 1, 2])
        self.assertEqual(rotate([1, 1, 2, 2], 1), [1, 2, 2, 1])

    def test_steps_wrap_modulo_length(self) -> None:
        for steps in (4, 7, 10**30):
            with self.subTest(steps=steps):
                self.assertEqual(rotate([1, 2, 3], steps), [2, 3, 1])

    def test_negative_steps_rotate_right(self) -> None:
        for steps, expected in (
            (-1, [3, 1, 2]),
            (-2, [2, 3, 1]),
            (-4, [3, 1, 2]),
            (-10**30, [3, 1, 2]),
        ):
            with self.subTest(steps=steps):
                self.assertEqual(rotate([1, 2, 3], steps), expected)

    def test_zero_and_full_rotations(self) -> None:
        for steps in (0, 3, -3, 6, -6):
            with self.subTest(steps=steps):
                self.assertEqual(rotate([1, 2, 3], steps), [1, 2, 3])

    def test_single_item(self) -> None:
        for steps in (0, 1, -1, 10**30, -10**30):
            with self.subTest(steps=steps):
                self.assertEqual(rotate([42], steps), [42])

    def test_empty_input(self) -> None:
        for steps in (0, 1, -1, 10**30, -10**30):
            with self.subTest(steps=steps):
                items: list[int] = []
                result = rotate(items, steps)
                self.assertEqual(result, [])
                self.assertEqual(items, [])
                self.assertIsNot(result, items)

    def test_returns_new_list_without_mutating_input(self) -> None:
        for steps in (0, 1, -1, 3, 4):
            with self.subTest(steps=steps):
                items = [1, 2, 3]
                result = rotate(items, steps)
                self.assertEqual(items, [1, 2, 3])
                self.assertIsNot(result, items)
                result.append(99)
                self.assertEqual(items, [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
