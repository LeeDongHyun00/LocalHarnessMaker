"""Regression coverage for the public rotate API."""

import unittest
from unittest.mock import call, patch

from solution import rotate, rotate_many


class RotateTests(unittest.TestCase):
    def test_positive_steps_rotate_left_modulo_length(self) -> None:
        for steps in (1, 4, 301):
            with self.subTest(steps=steps):
                self.assertEqual(rotate([1, 2, 3], steps), [2, 3, 1])

    def test_negative_steps_rotate_right(self) -> None:
        for steps in (-1, -4, -301):
            with self.subTest(steps=steps):
                self.assertEqual(rotate([1, 2, 3], steps), [3, 1, 2])

    def test_empty_input(self) -> None:
        for steps in (0, 1, -1, 100):
            with self.subTest(steps=steps):
                items: list[int] = []
                result = rotate(items, steps)
                self.assertEqual(result, [])
                self.assertIsNot(result, items)

    def test_zero_and_full_turns_return_independent_lists(self) -> None:
        for steps in (0, 3, -3):
            with self.subTest(steps=steps):
                items = [1, 2, 3]
                result = rotate(items, steps)
                self.assertEqual(result, items)
                self.assertIsNot(result, items)
                result.append(4)
                self.assertEqual(items, [1, 2, 3])

    def test_rotation_does_not_mutate_input(self) -> None:
        items = [1, 2, 3]
        result = rotate(items, 1)
        self.assertEqual(items, [1, 2, 3])
        result[0] = 99
        self.assertEqual(items, [1, 2, 3])

    def test_single_item(self) -> None:
        for steps in (0, 1, -1, 100):
            with self.subTest(steps=steps):
                self.assertEqual(rotate([7], steps), [7])


class RotateManyTests(unittest.TestCase):
    def test_results_follow_case_order(self) -> None:
        cases = [([1, 2, 3], 1), ([4, 5, 6], -1), ([], 9), ([7], 0)]
        self.assertEqual(rotate_many(cases), [[2, 3, 1], [6, 4, 5], [], [7]])

    def test_empty_batch(self) -> None:
        cases = []
        with patch("solution.rotate") as mock_rotate:
            result = rotate_many(cases)
        self.assertEqual(result, [])
        self.assertIsNot(result, cases)
        mock_rotate.assert_not_called()

    def test_cases_and_arguments_are_not_mutated(self) -> None:
        items = [1, 2, 3]
        cases = [(items, 1), (items, 0)]
        original_cases = cases.copy()
        results = rotate_many(cases)
        self.assertEqual(cases, original_cases)
        for case, original in zip(cases, original_cases):
            self.assertIs(case, original)
            self.assertIs(case[0], items)
        self.assertEqual(items, [1, 2, 3])
        self.assertIsNot(results[0], results[1])
        for result in results:
            self.assertIsNot(result, items)
            result.append(99)
        self.assertEqual(items, [1, 2, 3])

    def test_first_exception_propagates_unchanged_and_stops_batch(self) -> None:
        error = ValueError("first failure")
        cases = [([1, 2], 1), ([3, 4], 0), ([5, 6], -1)]
        with patch("solution.rotate", side_effect=[[2, 1], error, RuntimeError()]) as mock_rotate:
            with self.assertRaises(ValueError) as caught:
                rotate_many(cases)
        self.assertIs(caught.exception, error)
        self.assertEqual(mock_rotate.call_args_list, [call(*case) for case in cases[:2]])

    def test_invalid_positional_arguments_raise(self) -> None:
        for case in ((), ([1, 2],), ([1, 2], 1, 2), ([1, 2], "invalid")):
            with self.subTest(case=case):
                with self.assertRaises(TypeError):
                    rotate_many([case])


if __name__ == "__main__":
    unittest.main()
