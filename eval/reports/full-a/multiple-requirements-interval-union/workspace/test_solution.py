import unittest

from solution import union


class UnionTests(unittest.TestCase):
    def test_empty_input(self) -> None:
        self.assertEqual(union([]), [])

    def test_merges_overlapping_touching_and_nested_intervals(self) -> None:
        intervals = [(5, 8), (1, 3), (2, 4), (4, 5), (2, 2), (1, 3)]
        self.assertEqual(union(intervals), [(1, 8)])

    def test_disjoint_intervals_are_sorted_and_values_preserved(self) -> None:
        intervals = [(10**30, 10**30 + 1), (0, 0), (-8, -3), (2, 4)]
        self.assertEqual(
            union(intervals), [(-8, -3), (0, 0), (2, 4), (10**30, 10**30 + 1)]
        )

    def test_does_not_mutate_input_or_its_order(self) -> None:
        intervals = [(8, 10), (1, 4), (3, 9)]
        original = intervals.copy()
        self.assertEqual(union(intervals), [(1, 10)])
        self.assertEqual(intervals, original)

    def test_rejects_reversed_intervals_without_mutating_input(self) -> None:
        for intervals in ([(3, 2)], [(0, 10), (5, 4)], [(8, 9), (2, -1)]):
            with self.subTest(intervals=intervals):
                original = intervals.copy()
                with self.assertRaises(ValueError):
                    union(intervals)
                self.assertEqual(intervals, original)


if __name__ == "__main__":
    unittest.main()
