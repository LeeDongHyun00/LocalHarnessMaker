"""Regression tests for the public interval union API."""

import unittest
from copy import deepcopy
from unittest.mock import call, patch

from solution import union, union_many


class UnionTests(unittest.TestCase):
    def test_empty_input(self) -> None:
        self.assertEqual(union([]), [])

    def test_unsorted_overlapping_and_touching_intervals(self) -> None:
        self.assertEqual(
            union([(8, 10), (3, 5), (1, 3), (4, 8)]), [(1, 10)]
        )

    def test_disjoint_intervals_are_sorted_and_not_joined_across_gaps(self) -> None:
        self.assertEqual(union([(5, 7), (1, 2), (3, 4)]),
                         [(1, 2), (3, 4), (5, 7)])

    def test_nested_duplicate_negative_and_point_intervals(self) -> None:
        self.assertEqual(
            union([(0, 0), (-5, -1), (-3, -2), (-5, -1), (-1, 0), (2, 2)]),
            [(-5, 0), (2, 2)],
        )

    def test_reversed_interval_raises_value_error(self) -> None:
        for intervals in ([(2, 1)], [(0, 10), (5, 3)], [(4, 2), (0, 1)]):
            with self.subTest(intervals=intervals):
                original = intervals.copy()
                with self.assertRaises(ValueError):
                    union(intervals)
                self.assertEqual(intervals, original)

    def test_input_is_unchanged_and_result_is_independent(self) -> None:
        intervals = [(5, 6), (1, 3), (2, 5)]
        original = intervals.copy()
        result = union(intervals)
        self.assertEqual(result, [(1, 6)])
        self.assertEqual(intervals, original)
        result.append((9, 10))
        self.assertEqual(intervals, original)


class UnionManyTests(unittest.TestCase):
    def test_empty_batch(self) -> None:
        with patch("solution.union") as union_mock:
            self.assertEqual(union_many([]), [])
        union_mock.assert_not_called()

    def test_batch_results_follow_case_order_and_preserve_inputs(self) -> None:
        cases = [([(5, 7), (1, 3), (3, 5)],), ([],), ([(-2, -1)],)]
        original = deepcopy(cases)
        results = union_many(cases)
        self.assertEqual(results, [[(1, 7)], [], [(-2, -1)]])
        self.assertEqual(cases, original)
        results[2].append((8, 9))
        self.assertEqual(cases, original)

    def test_cases_are_unpacked_as_positional_arguments(self) -> None:
        cases = [("first", "second"), ()]
        with patch("solution.union", side_effect=["one", "two"]) as union_mock:
            self.assertEqual(union_many(cases), ["one", "two"])
        self.assertEqual(union_mock.call_args_list, [call("first", "second"), call()])

    def test_first_exception_is_propagated_unchanged_and_stops_batch(self) -> None:
        error = RuntimeError("sentinel")
        cases = [([],), ([(2, 1)],), ([(4, 5)],)]
        original = deepcopy(cases)
        with patch("solution.union", side_effect=[[], error, []]) as union_mock:
            with self.assertRaises(RuntimeError) as raised:
                union_many(cases)
        self.assertIs(raised.exception, error)
        self.assertEqual(union_mock.call_args_list, [call([]), call([(2, 1)])])
        self.assertEqual(cases, original)

    def test_union_validation_and_argument_errors_propagate(self) -> None:
        cases = [([(0, 1)],), ([(3, 2)],), ([(4, 5)],)]
        original = deepcopy(cases)
        with self.assertRaisesRegex(ValueError, "interval start must not exceed its end"):
            union_many(cases)
        self.assertEqual(cases, original)
        for case in ((), ([], [])):
            with self.subTest(case=case), self.assertRaises(TypeError):
                union_many([case])


if __name__ == "__main__":
    unittest.main()
