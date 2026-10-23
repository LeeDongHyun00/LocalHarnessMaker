import unittest

from solution import rotate, rotate_legacy


class RotateTests(unittest.TestCase):
    def test_rotations(self) -> None:
        cases = (
            (0, [1, 2, 3]),
            (1, [2, 3, 1]),
            (2, [3, 1, 2]),
            (3, [1, 2, 3]),
            (4, [2, 3, 1]),
            (-1, [3, 1, 2]),
            (-3, [1, 2, 3]),
            (-4, [3, 1, 2]),
            (10**30, [2, 3, 1]),
        )
        for function in (rotate, rotate_legacy):
            for steps, expected in cases:
                with self.subTest(function=function.__name__, steps=steps):
                    result = function([1, 2, 3], steps)
                    self.assertIs(type(result), list)
                    self.assertEqual(result, expected)

    def test_empty_input(self) -> None:
        for function in (rotate, rotate_legacy):
            for steps in (0, 4, -4, None, "invalid"):
                with self.subTest(function=function.__name__, steps=steps):
                    items: list[int] = []
                    result = function(items, steps)
                    self.assertEqual(result, [])
                    self.assertIs(type(result), list)
                    self.assertIsNot(result, items)
                    self.assertEqual(items, [])

    def test_input_is_unchanged_and_result_is_independent(self) -> None:
        for function in (rotate, rotate_legacy):
            for steps in (0, 1, 3, -1):
                with self.subTest(function=function.__name__, steps=steps):
                    items = [1, 2, 3]
                    result = function(items, steps)
                    self.assertEqual(items, [1, 2, 3])
                    self.assertIsNot(result, items)
                    result.append(4)
                    self.assertEqual(items, [1, 2, 3])

    def test_single_item(self) -> None:
        for function in (rotate, rotate_legacy):
            for steps in (0, 1, -1, 10**30):
                with self.subTest(function=function.__name__, steps=steps):
                    self.assertEqual(function([7], steps), [7])

    def test_invalid_steps_raise_type_error_for_nonempty_input(self) -> None:
        for function in (rotate, rotate_legacy):
            for steps in (None, "invalid", 1.0):
                with self.subTest(function=function.__name__, steps=steps):
                    items = [1, 2, 3]
                    with self.assertRaises(TypeError):
                        function(items, steps)
                    self.assertEqual(items, [1, 2, 3])

    def test_tuple_compatibility(self) -> None:
        for function in (rotate, rotate_legacy):
            with self.subTest(function=function.__name__):
                items = (1, 2, 3)
                result = function(items, 4)
                self.assertIs(type(result), tuple)
                self.assertEqual(result, (2, 3, 1))
                self.assertEqual(items, (1, 2, 3))
                self.assertEqual(function((), 4), [])


if __name__ == "__main__":
    unittest.main()
