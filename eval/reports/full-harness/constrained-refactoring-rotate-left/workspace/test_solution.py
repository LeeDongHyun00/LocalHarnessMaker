import unittest

from solution import rotate, rotate_legacy


class RotateTests(unittest.TestCase):
    def test_rotation_and_input_immutability(self):
        for function in (rotate, rotate_legacy):
            for steps, expected in (
                (0, [1, 2, 3]),
                (1, [2, 3, 1]),
                (4, [2, 3, 1]),
                (-1, [3, 1, 2]),
                (-4, [3, 1, 2]),
                (3, [1, 2, 3]),
            ):
                with self.subTest(function=function.__name__, steps=steps):
                    items = [1, 2, 3]
                    result = function(items, steps)
                    self.assertEqual(result, expected)
                    self.assertIsInstance(result, list)
                    self.assertIsNot(result, items)
                    self.assertEqual(items, [1, 2, 3])

    def test_empty_and_singleton_inputs(self):
        for function in (rotate, rotate_legacy):
            for items in ([], [7]):
                for steps in (0, 5, -5):
                    with self.subTest(
                        function=function.__name__, items=items, steps=steps
                    ):
                        result = function(items, steps)
                        self.assertEqual(result, items)
                        self.assertIsNot(result, items)

    def test_invalid_steps_preserve_error_and_input(self):
        for function in (rotate, rotate_legacy):
            for steps in (None, "1", 1.5):
                with self.subTest(function=function.__name__, steps=steps):
                    items = [1, 2, 3]
                    with self.assertRaises(TypeError):
                        function(items, steps)
                    self.assertEqual(items, [1, 2, 3])
                    # Empty inputs return before inspecting the steps argument.
                    self.assertEqual(function([], steps), [])


if __name__ == "__main__":
    unittest.main()
