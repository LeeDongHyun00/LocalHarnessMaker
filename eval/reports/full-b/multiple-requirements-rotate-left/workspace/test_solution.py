import unittest

from solution import rotate


class RotateTests(unittest.TestCase):
    def test_positive_steps_rotate_left_and_wrap(self) -> None:
        for steps in (1, 4, 7, 3 * 10**30 + 1):
            with self.subTest(steps=steps):
                self.assertEqual(rotate([1, 2, 3], steps), [2, 3, 1])

    def test_negative_steps_rotate_right_and_wrap(self) -> None:
        for steps in (-1, -4, -7, -(3 * 10**30 + 1)):
            with self.subTest(steps=steps):
                self.assertEqual(rotate([1, 2, 3], steps), [3, 1, 2])

    def test_zero_and_full_turns_preserve_order(self) -> None:
        for steps in (0, 3, 6, -3, -6):
            with self.subTest(steps=steps):
                self.assertEqual(rotate([1, 2, 3], steps), [1, 2, 3])

    def test_empty_input_returns_empty_list(self) -> None:
        for steps in (0, 1, 4, -1, -4):
            with self.subTest(steps=steps):
                items: list[int] = []
                result = rotate(items, steps)
                self.assertEqual(result, [])
                self.assertEqual(items, [])
                self.assertIsNot(result, items)

    def test_single_item(self) -> None:
        for steps in (0, 1, 4, -1, -4):
            with self.subTest(steps=steps):
                self.assertEqual(rotate([42], steps), [42])

    def test_input_is_unchanged_and_result_is_independent(self) -> None:
        for steps in (0, 1, 3, 4, -1, -3, -4):
            with self.subTest(steps=steps):
                items = [1, 2, 3]
                result = rotate(items, steps)
                self.assertEqual(items, [1, 2, 3])
                self.assertIsNot(result, items)
                result.append(99)
                self.assertEqual(items, [1, 2, 3])

    def test_preserves_values_duplicates_and_circular_order(self) -> None:
        items = [0, -5, 10**100, -5, 2]
        cases = (
            (2, [10**100, -5, 2, 0, -5]),
            (-2, [-5, 2, 0, -5, 10**100]),
        )
        for steps, expected in cases:
            with self.subTest(steps=steps):
                self.assertEqual(rotate(items, steps), expected)
                self.assertEqual(items, [0, -5, 10**100, -5, 2])


if __name__ == "__main__":
    unittest.main()
