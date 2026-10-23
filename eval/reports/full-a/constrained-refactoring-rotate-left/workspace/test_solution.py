import unittest

from solution import rotate, rotate_legacy


class RotateTests(unittest.TestCase):
    def test_rotation_steps(self) -> None:
        for function in (rotate, rotate_legacy):
            for steps, expected in (
                (0, [1, 2, 3]),
                (1, [2, 3, 1]),
                (3, [1, 2, 3]),
                (4, [2, 3, 1]),
                (-1, [3, 1, 2]),
                (-4, [3, 1, 2]),
            ):
                with self.subTest(function=function.__name__, steps=steps):
                    self.assertEqual(function([1, 2, 3], steps), expected)

    def test_input_is_unchanged_and_result_is_a_new_list(self) -> None:
        for function in (rotate, rotate_legacy):
            for steps in (0, 1, -1, 3):
                with self.subTest(function=function.__name__, steps=steps):
                    items = [1, 2, 3]
                    result = function(items, steps)
                    self.assertIsInstance(result, list)
                    self.assertIsNot(result, items)
                    self.assertEqual(items, [1, 2, 3])
                    result.append(4)
                    self.assertEqual(items, [1, 2, 3])

    def test_empty_input(self) -> None:
        for function in (rotate, rotate_legacy):
            for steps in (0, 4, -4):
                with self.subTest(function=function.__name__, steps=steps):
                    items: list[int] = []
                    result = function(items, steps)
                    self.assertEqual(result, [])
                    self.assertIsInstance(result, list)
                    self.assertIsNot(result, items)
                    self.assertEqual(items, [])

    def test_existing_error_behavior(self) -> None:
        for function in (rotate, rotate_legacy):
            for steps in (1.5, "1", None):
                with self.subTest(function=function.__name__, steps=steps):
                    items = [1, 2, 3]
                    with self.assertRaises(TypeError):
                        function(items, steps)
                    self.assertEqual(items, [1, 2, 3])
                    # Empty inputs return before inspecting the step value.
                    self.assertEqual(function([], steps), [])


if __name__ == "__main__":
    unittest.main()
