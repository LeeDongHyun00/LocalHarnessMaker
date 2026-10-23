"""Regression tests for the public windows API."""

import unittest
from unittest.mock import call, patch

from solution import windows, windows_many


class WindowsTests(unittest.TestCase):
    def test_overlapping_windows_advance_by_one(self) -> None:
        self.assertEqual(windows([1, 2, 3, 4], 2), [[1, 2], [2, 3], [3, 4]])

    def test_unit_and_full_length_windows(self) -> None:
        self.assertEqual(windows([1, 2, 3], 1), [[1], [2], [3]])
        self.assertEqual(windows([1, 2, 3], 3), [[1, 2, 3]])

    def test_oversized_windows_and_empty_input(self) -> None:
        self.assertEqual(windows([1, 2], 3), [])
        self.assertEqual(windows([], 1), [])

    def test_nonpositive_sizes_raise_value_error(self) -> None:
        for items in ([], [1, 2, 3]):
            for size in (0, -1, -10):
                with self.subTest(items=items, size=size):
                    with self.assertRaises(ValueError):
                        windows(items, size)

    def test_input_is_unchanged_and_windows_are_independent(self) -> None:
        items = [1, 2, 3]
        result = windows(items, 2)
        self.assertEqual(items, [1, 2, 3])
        result[0][1] = 99
        self.assertEqual(items, [1, 2, 3])
        self.assertEqual(result[1], [2, 3])


class WindowsManyTests(unittest.TestCase):
    def test_batch_results_follow_case_order(self) -> None:
        self.assertEqual(
            windows_many([([1, 2, 3], 2), ([], 1), ([4, 5], 1), ([6], 2)]),
            [[[1, 2], [2, 3]], [], [[4], [5]], []],
        )

    def test_empty_batch(self) -> None:
        self.assertEqual(windows_many([]), [])

    def test_cases_and_arguments_are_preserved(self) -> None:
        items = [1, 2, 3]
        cases = [(items, 2), (items, 1)]
        original_cases = cases.copy()
        result = windows_many(cases)
        self.assertEqual(cases, original_cases)
        self.assertEqual(items, [1, 2, 3])
        for case, original in zip(cases, original_cases):
            self.assertIs(case, original)
            self.assertIs(case[0], items)
        result[0][0][0] = 99
        self.assertEqual(items, [1, 2, 3])
        self.assertEqual(result[1], [[1], [2], [3]])

    def test_first_exception_is_propagated_unchanged_and_stops_batch(self) -> None:
        first_error = ValueError("first failure")
        later_error = RuntimeError("later failure")
        cases = [([1], 1), ([2], 0), ([3], -1)]
        with patch("solution.windows", side_effect=[[[1]], first_error, later_error]) as mocked:
            with self.assertRaises(ValueError) as caught:
                windows_many(cases)
        self.assertIs(caught.exception, first_error)
        self.assertEqual(mocked.call_args_list, [call([1], 1), call([2], 0)])
        self.assertEqual(cases, [([1], 1), ([2], 0), ([3], -1)])

    def test_validation_and_positional_argument_errors_propagate(self) -> None:
        with self.assertRaisesRegex(ValueError, "size must be positive"):
            windows_many([([1], 1), ([], 0)])
        for case in [(), ([1],), ([1], 1, 2)]:
            with self.subTest(case=case):
                with self.assertRaises(TypeError):
                    windows_many([case])


if __name__ == "__main__":
    unittest.main()
