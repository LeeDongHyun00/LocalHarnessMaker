"""Regression tests for the public interval union API."""

import unittest
from copy import deepcopy
from unittest.mock import call, patch

from solution import union, union_many


class UnionTests(unittest.TestCase):
    def test_merges_overlapping_and_touching_intervals(self) -> None:
        self.assertEqual(
            union([(8, 10), (2, 5), (4, 8), (1, 2)]), [(1, 10)]
        )

    def test_sorts_disjoint_intervals_without_merging_integer_neighbors(self) -> None:
        self.assertEqual(
            union([(7, 9), (2, 3), (-4, -1), (4, 6)]),
            [(-4, -1), (2, 3), (4, 6), (7, 9)],
        )

    def test_nested_duplicate_and_point_intervals(self) -> None:
        self.assertEqual(
            union([(1, 10), (2, 3), (1, 10), (10, 10), (12, 12)]),
            [(1, 10), (12, 12)],
        )

    def test_empty_input(self) -> None:
        self.assertEqual(union([]), [])

    def test_rejects_reversed_intervals_without_mutating_input(self) -> None:
        for intervals in ([(3, 2)], [(0, 10), (5, 4)], [(8, 9), (2, -1)]):
            with self.subTest(intervals=intervals):
                original = intervals.copy()
                with self.assertRaises(ValueError):
                    union(intervals)
                self.assertEqual(intervals, original)

    def test_does_not_mutate_input_and_returns_independent_list(self) -> None:
        intervals = [(8, 10), (1, 4), (3, 6)]
        original = intervals.copy()
        result = union(intervals)
        self.assertEqual(result, [(1, 6), (8, 10)])
        self.assertEqual(intervals, original)
        self.assertIsNot(result, intervals)
        result.append((20, 30))
        self.assertEqual(intervals, original)


class UnionManyTests(unittest.TestCase):
    def test_many_preserves_order_and_inputs(self) -> None:
        cases = [([(8, 10), (1, 4), (3, 6)],), ([],), ([(2, 3)],)]
        original = deepcopy(cases)
        results = union_many(cases)
        self.assertEqual(results, [[(1, 6), (8, 10)], [], [(2, 3)]])
        self.assertEqual(cases, original)
        results[0].append((20, 30))
        self.assertEqual(cases, original)

    def test_many_empty(self) -> None:
        with patch("solution.union") as mocked_union:
            self.assertEqual(union_many([]), [])
            mocked_union.assert_not_called()

    def test_many_propagates_first_exception_unchanged_and_stops(self) -> None:
        cases = [([(1, 2)],), ([(4, 3)],), ([(6, 5)],)]
        original = deepcopy(cases)
        error = ValueError("first failure")
        with patch("solution.union", side_effect=[[(1, 2)], error]) as mocked_union:
            with self.assertRaises(ValueError) as caught:
                union_many(cases)
            self.assertIs(caught.exception, error)
            self.assertEqual(mocked_union.call_args_list, [call(*case) for case in cases[:2]])
        self.assertEqual(cases, original)

    def test_many_invalid_interval_preserves_inputs(self) -> None:
        cases = [([(1, 2)],), ([(4, 3)],), ([(8, 9)],)]
        original = deepcopy(cases)
        with self.assertRaisesRegex(ValueError, "Interval start 4 exceeds end 3"):
            union_many(cases)
        self.assertEqual(cases, original)


if __name__ == "__main__":
    unittest.main()
