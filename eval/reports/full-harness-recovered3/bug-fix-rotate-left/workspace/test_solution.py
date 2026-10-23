import unittest

from solution import rotate


class RotateTests(unittest.TestCase):
    def test_rotation_and_input_preservation(self) -> None:
        for steps, expected in (
            (4, [2, 3, 1]),
            (-4, [3, 1, 2]),
            (0, [1, 2, 3]),
            (3, [1, 2, 3]),
        ):
            with self.subTest(steps=steps):
                items = [1, 2, 3]
                result = rotate(items, steps)
                self.assertEqual(result, expected)
                self.assertEqual(items, [1, 2, 3])
                self.assertIsNot(result, items)

    def test_empty_input(self) -> None:
        for steps in (0, 4, -4):
            with self.subTest(steps=steps):
                self.assertEqual(rotate([], steps), [])


if __name__ == "__main__":
    unittest.main()
