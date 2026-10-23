import unittest

from solution import rotate


class RotateTests(unittest.TestCase):
    def test_left_rotation_wraps_modulo_length(self) -> None:
        for steps in (1, 4, 3001):
            with self.subTest(steps=steps):
                self.assertEqual(rotate([1, 2, 3], steps), [2, 3, 1])

    def test_negative_steps_rotate_right(self) -> None:
        for steps in (-1, -4, -3001):
            with self.subTest(steps=steps):
                self.assertEqual(rotate([1, 2, 3], steps), [3, 1, 2])

    def test_empty_input(self) -> None:
        items: list[int] = []
        for steps in (0, 1, -1, 100):
            with self.subTest(steps=steps):
                result = rotate(items, steps)
                self.assertEqual(result, [])
                self.assertIsNot(result, items)
                self.assertEqual(items, [])

    def test_zero_and_full_turns_return_independent_lists(self) -> None:
        for steps in (0, 3, -3):
            with self.subTest(steps=steps):
                items = [1, 2, 3]
                result = rotate(items, steps)
                self.assertEqual(result, items)
                self.assertIsNot(result, items)
                result.append(4)
                self.assertEqual(items, [1, 2, 3])

    def test_preserves_values_order_and_input(self) -> None:
        items = [0, -7, 0, 42, -7]
        original = items.copy()
        self.assertEqual(rotate(items, 2), [0, 42, -7, 0, -7])
        self.assertEqual(items, original)

    def test_single_item(self) -> None:
        for steps in (0, 1, -1, 100, -100):
            with self.subTest(steps=steps):
                self.assertEqual(rotate([42], steps), [42])


if __name__ == "__main__":
    unittest.main()
