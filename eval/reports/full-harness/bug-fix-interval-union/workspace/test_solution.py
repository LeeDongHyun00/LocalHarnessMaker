import unittest

from solution import union


class UnionTests(unittest.TestCase):
    def test_merges_overlapping_touching_and_nested_intervals(self) -> None:
        intervals = [(8, 10), (3, 5), (1, 4), (2, 3), (5, 7), (12, 12)]
        original = intervals.copy()
        self.assertEqual(union(intervals), [(1, 7), (8, 10), (12, 12)])
        self.assertEqual(intervals, original)

    def test_empty_input(self) -> None:
        self.assertEqual(union([]), [])

    def test_rejects_reversed_interval_even_when_nested(self) -> None:
        intervals = [(0, 10), (5, 3)]
        with self.assertRaises(ValueError):
            union(intervals)
        self.assertEqual(intervals, [(0, 10), (5, 3)])


if __name__ == "__main__":
    unittest.main()
