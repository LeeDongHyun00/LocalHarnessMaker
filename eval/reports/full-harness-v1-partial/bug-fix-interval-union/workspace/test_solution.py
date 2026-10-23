import unittest

from solution import union


class UnionTests(unittest.TestCase):
    def test_merges_overlapping_touching_and_nested_intervals(self) -> None:
        intervals = [(8, 9), (3, 5), (1, 3), (2, 2), (12, 12), (5, 7)]
        original = intervals.copy()
        self.assertEqual(union(intervals), [(1, 7), (8, 9), (12, 12)])
        self.assertEqual(intervals, original)

    def test_empty_input(self) -> None:
        self.assertEqual(union([]), [])

    def test_invalid_interval_raises_without_mutating_input(self) -> None:
        intervals = [(1, 10), (5, 4)]
        original = intervals.copy()
        with self.assertRaises(ValueError):
            union(intervals)
        self.assertEqual(intervals, original)


if __name__ == "__main__":
    unittest.main()
