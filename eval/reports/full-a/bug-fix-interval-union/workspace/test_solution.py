import unittest

from solution import union


class UnionTests(unittest.TestCase):
    def test_merges_overlapping_touching_and_nested_intervals(self) -> None:
        intervals = [(8, 9), (3, 5), (1, 3), (2, 2), (7, 8)]
        original = intervals.copy()

        self.assertEqual(union(intervals), [(1, 5), (7, 9)])
        self.assertEqual(intervals, original)

    def test_empty_and_point_intervals(self) -> None:
        self.assertEqual(union([]), [])
        self.assertEqual(union([(2, 2), (2, 2)]), [(2, 2)])

    def test_rejects_reversed_interval_without_mutating_input(self) -> None:
        intervals = [(0, 10), (5, 3)]
        original = intervals.copy()

        with self.assertRaises(ValueError):
            union(intervals)
        self.assertEqual(intervals, original)


if __name__ == "__main__":
    unittest.main()
