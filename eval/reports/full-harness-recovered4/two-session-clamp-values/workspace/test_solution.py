"""Regression tests for the public clamp API."""

import unittest
from unittest.mock import call, patch

from solution import clamp, clamp_many


class ClampTests(unittest.TestCase):
    def test_values_within_inclusive_bounds(self) -> None:
        for value in (-5, 0, 5):
            with self.subTest(value=value):
                self.assertEqual(clamp(value, -5, 5), value)

    def test_value_below_lower_bound(self) -> None:
        self.assertEqual(clamp(-10, -5, 5), -5)

    def test_value_above_upper_bound(self) -> None:
        self.assertEqual(clamp(10, -5, 5), 5)

    def test_reversed_bounds_raise_value_error(self) -> None:
        for value in (-10, 0, 10):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    clamp(value, 5, -5)

    def test_equal_bounds_are_valid(self) -> None:
        for value in (-10, 3, 10):
            with self.subTest(value=value):
                self.assertEqual(clamp(value, 3, 3), 3)

    def test_processing_collection_preserves_inputs(self) -> None:
        values = [-10, 0, 10]
        original = values.copy()
        self.assertEqual([clamp(value, -5, 5) for value in values], [-5, 0, 5])
        self.assertEqual(values, original)


class ClampManyTests(unittest.TestCase):
    def test_batch_results_preserve_order_and_inputs(self) -> None:
        cases = [(10, -5, 5), (-10, -5, 5), (0, -5, 5), (3, 3, 3)]
        original = cases.copy()
        self.assertEqual(clamp_many(cases), [5, -5, 0, 3])
        self.assertEqual(cases, original)
        for case, saved in zip(cases, original):
            self.assertIs(case, saved)

    def test_batch_empty(self) -> None:
        self.assertEqual(clamp_many([]), [])

    def test_batch_invalid_arguments(self) -> None:
        with self.assertRaisesRegex(ValueError, "low must be less than or equal to high"):
            clamp_many([(0, -5, 5), (0, 5, -5)])
        with self.assertRaises(TypeError):
            clamp_many([(0, -5)])

    def test_batch_propagates_first_exception_unchanged_and_stops(self) -> None:
        cases = [(0, -5, 5), (1, -5, 5), (2, -5, 5)]
        original = cases.copy()
        error = RuntimeError("first failure")
        with patch("solution.clamp", side_effect=[0, error, AssertionError("later call")]) as mocked:
            with self.assertRaises(RuntimeError) as caught:
                clamp_many(cases)
        self.assertIs(caught.exception, error)
        self.assertEqual(mocked.call_args_list, [call(*cases[0]), call(*cases[1])])
        self.assertEqual(cases, original)


if __name__ == "__main__":
    unittest.main()
