import unittest

from solution import union


class UnionTests(unittest.TestCase):
    def test_merges_overlapping_and_touching_intervals(self) -> None:
        intervals = [(8, 10), (1, 4), (3, 6), (6, 8), (2, 3), (12, 12)]
        original = intervals.copy()

        self.assertEqual(union(intervals), [(1, 10), (12, 12)])
        self.assertEqual(intervals, original)

    def test_empty_input(self) -> None:
        self.assertEqual(union([]), [])

    def test_rejects_reversed_intervals(self) -> None:
        for intervals in [[(5, 2)], [(0, 10), (7, 3)], [(0, 1), (5, 2)]]:
            with self.subTest(intervals=intervals):
                original = intervals.copy()
                with self.assertRaises(ValueError):
                    union(intervals)
                self.assertEqual(intervals, original)


if __name__ == "__main__":
    unittest.main()
