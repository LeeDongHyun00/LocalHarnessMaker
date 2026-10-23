"""Regression tests for the public interval union API."""

import unittest
from copy import deepcopy
from unittest.mock import call, patch

from solution import union, union_many


class UnionTests(unittest.TestCase):
    def test_empty_input(self) -> None:
        self.assertEqual(union([]), [])

    def test_unsorted_overlapping_and_touching_intervals(self) -> None:
        intervals = [(8, 10), (3, 6), (1, 3), (5, 8)]
        self.assertEqual(union(intervals), [(1, 10)])

    def test_disjoint_intervals_are_sorted(self) -> None:
        self.assertEqual(union([(5, 7), (-4, -2), (0, 1)]),
                         [(-4, -2), (0, 1), (5, 7)])

    def test_nested_duplicate_and_point_intervals(self) -> None:
        self.assertEqual(union([(1, 10), (2, 3), (1, 10), (10, 10),
                                (12, 12)]), [(1, 10), (12, 12)])

    def test_point_interval_can_connect_touching_intervals(self) -> None:
        self.assertEqual(union([(-2, 0), (0, 0), (0, 2)]), [(-2, 2)])

    def test_reversed_endpoints_raise_value_error(self) -> None:
        for intervals in ([(3, 2)], [(0, 10), (5, 4)], [(0, 1), (-1, -2)]):
            with self.subTest(intervals=intervals):
                original = intervals.copy()
                with self.assertRaises(ValueError):
                    union(intervals)
                self.assertEqual(intervals, original)

    def test_input_is_unchanged_and_result_is_independent(self) -> None:
        intervals = [(5, 8), (1, 3), (3, 6)]
        original = intervals.copy()
        result = union(intervals)
        self.assertEqual(result, [(1, 8)])
        self.assertEqual(intervals, original)
        self.assertIsNot(result, intervals)
        result.append((20, 21))
        self.assertEqual(intervals, original)


class UnionManyTests(unittest.TestCase):
    def test_empty_cases(self) -> None:
        with patch("solution.union") as mocked_union:
            self.assertEqual(union_many([]), [])
        mocked_union.assert_not_called()

    def test_batch_results_follow_case_order_and_preserve_inputs(self) -> None:
        intervals = [(8, 10), (1, 3), (3, 8)]
        cases = [(intervals,), ([],), ([(5, 6), (-2, 0)],), (intervals,)]
        original = deepcopy(cases)
        result = union_many(cases)
        self.assertEqual(result, [[(1, 10)], [], [(-2, 0), (5, 6)], [(1, 10)]])
        self.assertEqual(cases, original)
        self.assertIs(cases[0][0], intervals)
        result[0].append((20, 21))
        self.assertEqual(result[3], [(1, 10)])
        self.assertEqual(cases, original)

    def test_first_exception_is_propagated_unchanged_and_stops_batch(self) -> None:
        error = ValueError("sentinel")
        cases = [([(1, 2)],), ([(4, 3)],), ([(5, 6)],)]
        original = deepcopy(cases)
        with patch("solution.union", side_effect=[[(1, 2)], error]) as mocked_union:
            with self.assertRaises(ValueError) as raised:
                union_many(cases)
        self.assertIs(raised.exception, error)
        self.assertEqual(mocked_union.call_args_list,
                         [call(*cases[0]), call(*cases[1])])
        self.assertEqual(cases, original)

    def test_invalid_intervals_preserve_batch_inputs(self) -> None:
        cases = [([(2, 4), (0, 2)],), ([(0, 10), (5, 4)],)]
        original = deepcopy(cases)
        with self.assertRaisesRegex(ValueError, "interval start"):
            union_many(cases)
        self.assertEqual(cases, original)

    def test_each_tuple_is_expanded_as_positional_arguments(self) -> None:
        for case in ((), ([], [])):
            with self.subTest(case=case):
                with self.assertRaises(TypeError):
                    union_many([case])


if __name__ == "__main__":
    unittest.main()
