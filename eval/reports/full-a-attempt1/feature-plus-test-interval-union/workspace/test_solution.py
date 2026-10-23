"""Tests for the public interval union API."""

import unittest

from solution import union


class UnionTests(unittest.TestCase):
    def test_unsorted_overlapping_and_disjoint_intervals(self) -> None:
        self.assertEqual(
            union([(8, 10), (2, 6), (15, 18), (1, 3)]),
            [(1, 6), (8, 10), (15, 18)],
        )

    def test_touching_chain_merges(self) -> None:
        self.assertEqual(union([(4, 7), (1, 2), (2, 4)]), [(1, 7)])

    def test_nested_duplicate_and_point_intervals(self) -> None:
        self.assertEqual(
            union([(1, 10), (2, 3), (1, 10), (10, 10), (12, 12)]),
            [(1, 10), (12, 12)],
        )

    def test_negative_and_zero_endpoints(self) -> None:
        self.assertEqual(union([(-3, 0), (-5, -3), (0, 2)]), [(-5, 2)])

    def test_empty_input(self) -> None:
        self.assertEqual(union([]), [])

    def test_single_point(self) -> None:
        self.assertEqual(union([(0, 0)]), [(0, 0)])

    def test_integer_neighbors_remain_separate(self) -> None:
        self.assertEqual(union([(1, 2), (3, 4)]), [(1, 2), (3, 4)])

    def test_reversed_intervals_raise_value_error(self) -> None:
        for intervals in ([(2, 1)], [(0, 10), (5, 4)], [(-1, -2)]):
            with self.subTest(intervals=intervals):
                original = intervals.copy()
                with self.assertRaises(ValueError):
                    union(intervals)
                self.assertEqual(intervals, original)

    def test_input_is_preserved_and_result_is_independent(self) -> None:
        intervals = [(5, 8), (1, 5), (10, 11)]
        original = intervals.copy()
        result = union(intervals)
        self.assertEqual(intervals, original)
        self.assertEqual(result, [(1, 8), (10, 11)])
        self.assertIsNot(result, intervals)
        result.append((20, 30))
        self.assertEqual(intervals, original)


if __name__ == "__main__":
    unittest.main()
