"""Regression tests for the public rotate API."""

import unittest
from unittest.mock import call, patch

from solution import rotate, rotate_many


class RotateTests(unittest.TestCase):
    def test_positive_steps(self):
        for steps, expected in ((1, [2, 3, 1]), (4, [2, 3, 1]), (8, [3, 1, 2])):
            with self.subTest(steps=steps):
                self.assertEqual(rotate([1, 2, 3], steps), expected)

    def test_negative_steps(self):
        for steps, expected in ((-1, [3, 1, 2]), (-4, [3, 1, 2]), (-8, [2, 3, 1])):
            with self.subTest(steps=steps):
                self.assertEqual(rotate([1, 2, 3], steps), expected)

    def test_empty_input(self):
        for steps in (0, 5, -5):
            with self.subTest(steps=steps):
                self.assertEqual(rotate([], steps), [])

    def test_zero_and_full_rotations(self):
        for steps in (0, 3, -3, 300):
            with self.subTest(steps=steps):
                self.assertEqual(rotate([1, 2, 3], steps), [1, 2, 3])

    def test_single_item(self):
        self.assertEqual(rotate([42], -100), [42])

    def test_input_is_preserved_and_result_is_new(self):
        for steps in (0, 1, -1, 3):
            with self.subTest(steps=steps):
                source = [1, 2, 3]
                result = rotate(source, steps)
                self.assertEqual(source, [1, 2, 3])
                self.assertIsNot(result, source)
                result.append(4)
                self.assertEqual(source, [1, 2, 3])
        source = []
        self.assertIsNot(rotate(source, 5), source)


class RotateManyTests(unittest.TestCase):
    def test_batch_results_preserve_order_and_inputs(self):
        cases = [([1, 2, 3], 1), ([4, 5, 6], -1), ([], 5), ([7], 0)]
        original_cases = list(cases)
        original_items = [items.copy() for items, _ in cases]

        results = rotate_many(cases)

        self.assertEqual(results, [[2, 3, 1], [6, 4, 5], [], [7]])
        self.assertEqual(cases, original_cases)
        for case, original_case, original, result in zip(
            cases, original_cases, original_items, results
        ):
            self.assertIs(case, original_case)
            self.assertEqual(case[0], original)
            self.assertIsNot(result, case[0])
            result.append(99)
            self.assertEqual(case[0], original)

    def test_empty_batch(self):
        cases = []
        self.assertEqual(rotate_many(cases), [])
        self.assertEqual(cases, [])

    def test_first_exception_is_propagated_unchanged(self):
        first_error = ValueError("first failure")
        later_error = RuntimeError("later failure")
        cases = [([1, 2], 1), ([3, 4], 0), ([5, 6], -1)]
        with patch("solution.rotate", side_effect=[[2, 1], first_error, later_error]) as mock:
            with self.assertRaises(ValueError) as raised:
                rotate_many(cases)
        self.assertIs(raised.exception, first_error)
        self.assertEqual(mock.call_args_list, [call(*cases[0]), call(*cases[1])])
        self.assertEqual(cases, [([1, 2], 1), ([3, 4], 0), ([5, 6], -1)])

    def test_invalid_argument_count_uses_rotate_error(self):
        with self.assertRaises(TypeError):
            rotate_many([([1, 2, 3],)])


if __name__ == "__main__":
    unittest.main()
