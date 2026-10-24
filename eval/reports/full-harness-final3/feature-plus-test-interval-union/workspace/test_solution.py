"""Tests for the public interval union API."""

import unittest

from solution import union


class UnionTests(unittest.TestCase):
    def test_unsorted_overlapping_and_disjoint_intervals(self) -> None:
        intervals = [(8, 10), (2, 6), (1, 3), (15, 18)]
        original = intervals.copy()
        self.assertEqual(union(intervals), [(1, 6), (8, 10), (15, 18)])
        self.assertEqual(intervals, original)

    def test_touching_nested_duplicate_and_point_intervals(self) -> None:
        intervals = [(4, 4), (1, 3), (2, 2), (3, 4), (1, 3)]
        self.assertEqual(union(intervals), [(1, 4)])

    def test_negative_endpoints_and_separate_points(self) -> None:
        self.assertEqual(
            union([(2, 2), (-3, -1), (0, 0), (-1, 0)]),
            [(-3, 0), (2, 2)],
        )

    def test_empty_input(self) -> None:
        intervals: list[tuple[int, int]] = []
        result = union(intervals)
        self.assertEqual(result, [])
        self.assertIsNot(result, intervals)

    def test_single_interval(self) -> None:
        self.assertEqual(union([(5, 5)]), [(5, 5)])
        self.assertEqual(union([(1, 7)]), [(1, 7)])

    def test_reversed_interval_raises_without_mutation(self) -> None:
        for intervals in [[(3, 2)], [(0, 10), (5, 4)], [(8, 9), (-1, -2)]]:
            with self.subTest(intervals=intervals):
                original = intervals.copy()
                with self.assertRaises(ValueError):
                    union(intervals)
                self.assertEqual(intervals, original)


if __name__ == "__main__":
    unittest.main()
