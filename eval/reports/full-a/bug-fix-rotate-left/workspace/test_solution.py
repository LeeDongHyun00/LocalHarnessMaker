import unittest

from solution import rotate


class RotateTests(unittest.TestCase):
    def test_rotation_wraps_and_preserves_input(self) -> None:
        items = [1, 2, 3]
        for steps, expected in (
            (4, [2, 3, 1]),
            (-4, [3, 1, 2]),
            (0, [1, 2, 3]),
            (3, [1, 2, 3]),
        ):
            with self.subTest(steps=steps):
                result = rotate(items, steps)
                self.assertEqual(result, expected)
                self.assertEqual(items, [1, 2, 3])
                self.assertIsNot(result, items)

    def test_empty_input(self) -> None:
        self.assertEqual(rotate([], 4), [])


if __name__ == "__main__":
    unittest.main()
