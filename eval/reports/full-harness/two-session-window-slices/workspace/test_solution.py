"""Regression tests for the public windows API."""

import unittest
from unittest.mock import call, patch

from solution import windows, windows_many


class WindowsTests(unittest.TestCase):
    def test_overlapping_windows(self):
        self.assertEqual(windows([1, 2, 3, 4], 2), [[1, 2], [2, 3], [3, 4]])

    def test_size_one(self):
        self.assertEqual(windows([1, 2, 3], 1), [[1], [2], [3]])

    def test_size_equals_length(self):
        self.assertEqual(windows([1, 2, 3], 3), [[1, 2, 3]])

    def test_size_exceeds_length(self):
        self.assertEqual(windows([1, 2], 3), [])

    def test_empty_input(self):
        self.assertEqual(windows([], 1), [])

    def test_nonpositive_size(self):
        for items in ([], [1, 2, 3]):
            for size in (0, -1, -5):
                with self.subTest(items=items, size=size):
                    with self.assertRaises(ValueError):
                        windows(items, size)

    def test_input_preserved_and_windows_independent(self):
        items = [1, 2, 3]
        result = windows(items, 2)
        self.assertEqual(items, [1, 2, 3])
        result[0][1] = 99
        self.assertEqual(items, [1, 2, 3])
        self.assertEqual(result[1], [2, 3])


class WindowsManyTests(unittest.TestCase):
    def test_batch_results_in_case_order(self):
        cases = [([1, 2, 3], 2), ([], 1), ([4, 5], 1), ([6], 2)]
        self.assertEqual(
            windows_many(cases),
            [[[1, 2], [2, 3]], [], [[4], [5]], []],
        )

    def test_batch_empty(self):
        self.assertEqual(windows_many([]), [])

    def test_batch_preserves_cases_and_arguments(self):
        items = [1, 2, 3]
        cases = [(items, 2), (items, 1)]
        original_cases = cases[:]
        result = windows_many(cases)
        self.assertEqual(cases, [([1, 2, 3], 2), ([1, 2, 3], 1)])
        for actual, original in zip(cases, original_cases):
            self.assertIs(actual, original)
            self.assertIs(actual[0], items)
        result[0][0][0] = 99
        self.assertEqual(items, [1, 2, 3])
        self.assertEqual(result[1], [[1], [2], [3]])

    def test_batch_propagates_first_exception_unchanged(self):
        first_error = ValueError("first failure")
        later_error = RuntimeError("later failure")
        cases = [([1], 1), ([2], 0), ([3], -1)]
        with patch("solution.windows", side_effect=[[[1]], first_error, later_error]) as mocked:
            with self.assertRaises(ValueError) as caught:
                windows_many(cases)
            self.assertIs(caught.exception, first_error)
            self.assertEqual(mocked.call_args_list, [call([1], 1), call([2], 0)])
        self.assertEqual(cases, [([1], 1), ([2], 0), ([3], -1)])

    def test_batch_delegates_validation(self):
        with self.assertRaisesRegex(ValueError, "size must be positive"):
            windows_many([([1], 1), ([], 0)])
        with self.assertRaises(TypeError):
            windows_many([([1],)])


if __name__ == "__main__":
    unittest.main()
