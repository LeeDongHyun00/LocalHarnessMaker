"""Regression tests for the public clamp API."""

import unittest
from unittest.mock import call, patch

from solution import clamp, clamp_many


class ClampTests(unittest.TestCase):
    def test_values_inside_range_are_unchanged(self) -> None:
        for value in (-4, 0, 6):
            with self.subTest(value=value):
                self.assertEqual(clamp(value, -5, 7), value)

    def test_values_outside_range_use_nearest_bound(self) -> None:
        self.assertEqual(clamp(-10, -5, 7), -5)
        self.assertEqual(clamp(10, -5, 7), 7)

    def test_endpoints_are_inclusive(self) -> None:
        self.assertEqual(clamp(-5, -5, 7), -5)
        self.assertEqual(clamp(7, -5, 7), 7)

    def test_equal_bounds_are_valid(self) -> None:
        for value in (-10, 3, 10):
            with self.subTest(value=value):
                self.assertEqual(clamp(value, 3, 3), 3)

    def test_reversed_bounds_raise_value_error(self) -> None:
        for value in (-10, 0, 10):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    clamp(value, 5, -5)


class ClampManyTests(unittest.TestCase):
    def test_results_follow_case_order(self) -> None:
        cases = [(10, -5, 7), (0, -5, 7), (-10, -5, 7), (3, 3, 3)]
        self.assertEqual(clamp_many(cases), [7, 0, -5, 3])

    def test_empty_cases(self) -> None:
        self.assertEqual(clamp_many([]), [])

    def test_cases_and_mutable_arguments_are_unchanged(self) -> None:
        value, low, high = [2], [1], [3]
        case = (value, low, high)
        cases = [case]
        self.assertIs(clamp_many(cases)[0], value)
        self.assertEqual(cases, [([2], [1], [3])])
        self.assertIs(cases[0], case)
        for actual, original in zip(case, (value, low, high)):
            self.assertIs(actual, original)

    def test_invalid_cases_propagate_clamp_errors(self) -> None:
        for invalid, error_type in [((0, 5, -5), ValueError), ((0, 5), TypeError)]:
            with self.subTest(invalid=invalid):
                with self.assertRaises(error_type):
                    clamp_many([(0, -5, 5), invalid])

    def test_first_exception_is_unchanged_and_stops_processing(self) -> None:
        error = RuntimeError("sentinel")
        cases = [(0, -5, 5), (1, -5, 5), (2, -5, 5)]
        with patch("solution.clamp", side_effect=[0, error, 2]) as mocked_clamp:
            with self.assertRaises(RuntimeError) as caught:
                clamp_many(cases)
        self.assertIs(caught.exception, error)
        self.assertEqual(mocked_clamp.call_args_list, [call(*case) for case in cases[:2]])


if __name__ == "__main__":
    unittest.main()
