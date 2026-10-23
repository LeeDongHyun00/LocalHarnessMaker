"""Tests for the public interval union API."""

import unittest

from solution import union


class UnionTests(unittest.TestCase):
    def test_merges_overlapping_intervals_in_start_order(self) -> None:
        intervals = [(8, 10), (1, 3), (2, 6), (15, 18), (4, 5)]
        self.assertEqual(union(intervals), [(1, 6), (8, 10), (15, 18)])

    def test_merges_touching_endpoints_but_preserves_gaps(self) -> None:
        intervals = [(-3, -1), (-1, 2), (2, 2), (3, 3), (4, 5), (5, 7)]
        self.assertEqual(union(intervals), [(-3, 2), (3, 3), (4, 7)])

    def test_nested_duplicate_and_single_intervals(self) -> None:
        cases = [
            ([(0, 10), (2, 3), (0, 5), (0, 10)], [(0, 10)]),
            ([(4, 4), (4, 4)], [(4, 4)]),
            ([(-5, -2)], [(-5, -2)]),
            ([(0, 0)], [(0, 0)]),
        ]
        for intervals, expected in cases:
            with self.subTest(intervals=intervals):
                self.assertEqual(union(intervals), expected)

    def test_empty_input(self) -> None:
        self.assertEqual(union([]), [])

    def test_does_not_mutate_input(self) -> None:
        intervals = [(8, 10), (1, 4), (3, 9), (15, 15)]
        original = intervals.copy()
        self.assertEqual(union(intervals), [(1, 10), (15, 15)])
        self.assertEqual(intervals, original)

    def test_rejects_reversed_intervals_without_mutating_input(self) -> None:
        cases = [
            [(3, 2)],
            [(0, 10), (5, 4)],
            [(10, 9), (-2, 0)],
            [(-1, -3)],
        ]
        for intervals in cases:
            with self.subTest(intervals=intervals):
                original = intervals.copy()
                with self.assertRaises(ValueError):
                    union(intervals)
                self.assertEqual(intervals, original)


if __name__ == "__main__":
    unittest.main()
