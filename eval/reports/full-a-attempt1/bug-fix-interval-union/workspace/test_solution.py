import unittest

from solution import union


class UnionTests(unittest.TestCase):
    def test_merges_overlapping_touching_and_nested_intervals(self) -> None:
        intervals = [(8, 9), (3, 5), (1, 4), (5, 6), (2, 3), (8, 8)]
        original = intervals.copy()

        self.assertEqual(union(intervals), [(1, 6), (8, 9)])
        self.assertEqual(intervals, original)

    def test_empty_input(self) -> None:
        self.assertEqual(union([]), [])

    def test_invalid_interval_raises_without_mutating_input(self) -> None:
        intervals = [(1, 10), (5, 3)]
        original = intervals.copy()

        with self.assertRaises(ValueError):
            union(intervals)
        self.assertEqual(intervals, original)


if __name__ == "__main__":
    unittest.main()
