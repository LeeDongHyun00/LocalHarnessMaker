"""Tests for the public interval union API."""

import unittest

from solution import union


class UnionTests(unittest.TestCase):
    def test_unsorted_overlapping_and_disjoint_intervals(self) -> None:
        intervals = [(8, 10), (2, 6), (15, 18), (1, 3)]
        self.assertEqual(union(intervals), [(1, 6), (8, 10), (15, 18)])

    def test_touching_nested_duplicate_and_point_intervals(self) -> None:
        cases = [
            ([(3, 5), (1, 3), (5, 7)], [(1, 7)]),
            ([(1, 10), (2, 3), (1, 10)], [(1, 10)]),
            ([(-3, -1), (-1, -1), (-1, 0), (2, 2)], [(-3, 0), (2, 2)]),
            ([(1, 2), (3, 4)], [(1, 2), (3, 4)]),
            ([(0, 0)], [(0, 0)]),
        ]
        for intervals, expected in cases:
            with self.subTest(intervals=intervals):
                self.assertEqual(union(intervals), expected)

    def test_empty_input(self) -> None:
        self.assertEqual(union([]), [])

    def test_invalid_interval_raises_value_error(self) -> None:
        for intervals in [[(3, 2)], [(0, 10), (5, 4)], [(2, 1), (0, 3)]]:
            with self.subTest(intervals=intervals):
                original = intervals.copy()
                with self.assertRaises(ValueError):
                    union(intervals)
                self.assertEqual(intervals, original)

    def test_input_is_preserved_and_result_is_independent(self) -> None:
        intervals = [(5, 8), (1, 3), (3, 6)]
        original = intervals.copy()
        result = union(intervals)
        self.assertEqual(result, [(1, 8)])
        self.assertEqual(intervals, original)
        self.assertIsNot(result, intervals)
        result.append((20, 30))
        self.assertEqual(intervals, original)


if __name__ == "__main__":
    unittest.main()
