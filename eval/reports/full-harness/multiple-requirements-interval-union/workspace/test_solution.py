import unittest

from solution import union


class UnionTests(unittest.TestCase):
    def test_merges_overlapping_and_touching_intervals_in_start_order(self) -> None:
        intervals = [(8, 10), (3, 5), (12, 14), (1, 3), (4, 8), (-4, -2)]
        self.assertEqual(union(intervals), [(-4, -2), (1, 10), (12, 14)])

    def test_nested_duplicate_and_point_intervals(self) -> None:
        self.assertEqual(
            union([(2, 3), (1, 10), (1, 10), (10, 10), (12, 12)]),
            [(1, 10), (12, 12)],
        )

    def test_empty_input(self) -> None:
        self.assertEqual(union([]), [])

    def test_invalid_interval_raises_and_preserves_input(self) -> None:
        intervals = [(7, 9), (5, 2), (1, 4)]
        original = intervals.copy()
        with self.assertRaises(ValueError):
            union(intervals)
        self.assertEqual(intervals, original)

    def test_preserves_input_values_and_collection_order(self) -> None:
        intervals = [(8, 9), (1, 4), (3, 8)]
        original = intervals.copy()
        result = union(intervals)
        self.assertEqual(result, [(1, 9)])
        self.assertEqual(intervals, original)
        self.assertIsNot(result, intervals)
        for interval, saved in zip(intervals, original):
            self.assertIs(interval, saved)


if __name__ == "__main__":
    unittest.main()
