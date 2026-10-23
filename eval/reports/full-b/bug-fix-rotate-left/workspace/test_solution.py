import unittest

from solution import rotate


class RotateTests(unittest.TestCase):
    def test_rotate_steps_without_mutating_input(self) -> None:
        for steps, expected in (
            (1, [2, 3, 1]),
            (4, [2, 3, 1]),
            (-1, [3, 1, 2]),
            (-4, [3, 1, 2]),
            (0, [1, 2, 3]),
            (6, [1, 2, 3]),
            (-6, [1, 2, 3]),
        ):
            with self.subTest(steps=steps):
                items = [1, 2, 3]
                self.assertEqual(rotate(items, steps), expected)
                self.assertEqual(items, [1, 2, 3])

    def test_rotate_empty_input(self) -> None:
        for steps in (0, 4, -4):
            with self.subTest(steps=steps):
                self.assertEqual(rotate([], steps), [])


if __name__ == "__main__":
    unittest.main()
