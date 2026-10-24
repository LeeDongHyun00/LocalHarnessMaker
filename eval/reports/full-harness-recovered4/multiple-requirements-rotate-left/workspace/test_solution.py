import unittest

from solution import rotate


class RotateTests(unittest.TestCase):
    def test_left_rotation_modulo_length(self) -> None:
        for steps in (1, 4, 10):
            with self.subTest(steps=steps):
                self.assertEqual(rotate([1, 2, 3], steps), [2, 3, 1])

    def test_negative_steps_rotate_right(self) -> None:
        for steps in (-1, -4, -10):
            with self.subTest(steps=steps):
                self.assertEqual(rotate([1, 2, 3], steps), [3, 1, 2])

    def test_empty_input(self) -> None:
        items: list[int] = []
        for steps in (0, 4, -4):
            with self.subTest(steps=steps):
                result = rotate(items, steps)
                self.assertEqual(result, [])
                self.assertIsNot(result, items)
                self.assertEqual(items, [])

    def test_values_order_and_input_are_preserved(self) -> None:
        items = [7, -2, 7, 0, 9]
        original = items.copy()
        result = rotate(items, 2)
        self.assertEqual(result, [7, 0, 9, 7, -2])
        self.assertEqual(items, original)
        self.assertIsNot(result, items)
        result[0] = 100
        self.assertEqual(items, original)

    def test_zero_full_turns_and_singleton(self) -> None:
        for items in ([1, 2, 3], [5]):
            for steps in (0, len(items), -len(items)):
                with self.subTest(items=items, steps=steps):
                    result = rotate(items, steps)
                    self.assertEqual(result, items)
                    self.assertIsNot(result, items)


if __name__ == "__main__":
    unittest.main()
