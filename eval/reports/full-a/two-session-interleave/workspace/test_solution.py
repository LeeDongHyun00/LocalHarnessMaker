"""Regression tests for the public interleave API."""

import unittest
from unittest.mock import call, patch

from solution import interleave, interleave_many


class InterleaveTests(unittest.TestCase):
    def test_equal_lengths_start_with_left(self) -> None:
        self.assertEqual(interleave([1, 2, 3], [10, 20, 30]),
                         [1, 10, 2, 20, 3, 30])

    def test_left_remainder_preserves_order(self) -> None:
        self.assertEqual(interleave([1, 2, 3, 4], [10]),
                         [1, 10, 2, 3, 4])

    def test_right_remainder_preserves_order(self) -> None:
        self.assertEqual(interleave([1], [10, 20, 30, 40]),
                         [1, 10, 20, 30, 40])

    def test_empty_inputs(self) -> None:
        for left, right, expected in (
            ([], [], []),
            ([], [1, 2], [1, 2]),
            ([1, 2], [], [1, 2]),
        ):
            with self.subTest(left=left, right=right):
                self.assertEqual(interleave(left, right), expected)

    def test_inputs_are_unchanged_and_result_is_independent(self) -> None:
        left = [1, 2, 3]
        right = [4, 5]
        result = interleave(left, right)
        self.assertEqual(result, [1, 4, 2, 5, 3])
        self.assertEqual(left, [1, 2, 3])
        self.assertEqual(right, [4, 5])
        result.append(99)
        self.assertEqual(left, [1, 2, 3])
        self.assertEqual(right, [4, 5])

    def test_same_list_can_be_both_inputs(self) -> None:
        values = [0, -1, 0]
        self.assertEqual(interleave(values, values), [0, 0, -1, -1, 0, 0])
        self.assertEqual(values, [0, -1, 0])


class InterleaveManyTests(unittest.TestCase):
    def test_batch_results_follow_case_order(self) -> None:
        cases = [([1, 2], [10]), ([], [3, 4]), ([5], []), ([], [])]
        self.assertEqual(interleave_many(cases),
                         [[1, 10, 2], [3, 4], [5], []])

    def test_empty_batch(self) -> None:
        with patch("solution.interleave") as single:
            self.assertEqual(interleave_many([]), [])
            single.assert_not_called()

    def test_cases_and_aliased_arguments_are_unchanged(self) -> None:
        values = [1, 2]
        other = [3]
        case = (values, other)
        cases = [case, (values, values), case]
        original_cases = cases.copy()
        results = interleave_many(cases)
        self.assertEqual(results, [[1, 3, 2], [1, 1, 2, 2], [1, 3, 2]])
        self.assertEqual(cases, original_cases)
        for actual, original in zip(cases, original_cases):
            self.assertIs(actual, original)
        self.assertEqual(values, [1, 2])
        self.assertEqual(other, [3])
        results[0].append(99)
        self.assertEqual(results[2], [1, 3, 2])
        self.assertEqual(values, [1, 2])
        self.assertEqual(other, [3])

    def test_first_exception_is_propagated_unchanged_and_stops_batch(self) -> None:
        cases = [([1], [2]), ([3], [4]), ([5], [6])]
        error = ValueError("original error")
        with patch("solution.interleave", side_effect=[[1, 2], error]) as single:
            with self.assertRaises(ValueError) as caught:
                interleave_many(cases)
            self.assertIs(caught.exception, error)
            self.assertEqual(single.call_args_list,
                             [call(*cases[0]), call(*cases[1])])

    def test_invalid_positional_arguments_raise_type_error(self) -> None:
        for case in ((), ([1],), ([1], [2], [3])):
            with self.subTest(case=case):
                with self.assertRaises(TypeError):
                    interleave_many([case])


if __name__ == "__main__":
    unittest.main()
