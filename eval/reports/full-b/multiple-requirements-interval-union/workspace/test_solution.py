import unittest

from solution import union


class UnionTests(unittest.TestCase):
    def test_empty_input(self) -> None:
        self.assertEqual(union([]), [])

    def test_disjoint_intervals_are_sorted_by_start(self) -> None:
        intervals = [(8, 10), (4, 5), (-6, -4), (2, 3)]
        self.assertEqual(union(intervals), [(-6, -4), (2, 3), (4, 5), (8, 10)])

    def test_overlaps_merge_transitively(self) -> None:
        self.assertEqual(union([(8, 12), (1, 4), (3, 9)]), [(1, 12)])

    def test_touching_closed_intervals_merge(self) -> None:
        self.assertEqual(union([(6, 9), (2, 5), (1, 2), (5, 6)]), [(1, 9)])

    def test_nested_intervals_duplicates_and_equal_starts(self) -> None:
        intervals = [(1, 4), (2, 3), (1, 10), (1, 10), (6, 7)]
        self.assertEqual(union(intervals), [(1, 10)])

    def test_zero_length_intervals(self) -> None:
        intervals = [(4, 4), (1, 1), (1, 3), (3, 3), (7, 7)]
        self.assertEqual(union(intervals), [(1, 3), (4, 4), (7, 7)])

    def test_preserves_large_and_negative_endpoint_values(self) -> None:
        limit = 10**80
        intervals = [
            (limit, limit + 1),
            (-limit, -limit + 2),
            (limit - 2, limit),
            (-limit + 1, -limit + 3),
        ]
        self.assertEqual(
            union(intervals), [(-limit, -limit + 3), (limit - 2, limit + 1)]
        )

    def test_input_values_and_order_are_unchanged(self) -> None:
        intervals = [(8, 11), (2, 5), (4, 9), (-3, -1)]
        original = intervals.copy()

        result = union(intervals)

        self.assertEqual(result, [(-3, -1), (2, 11)])
        self.assertEqual(intervals, original)
        self.assertIsNot(result, intervals)

    def test_invalid_intervals_raise_without_mutating_input(self) -> None:
        cases = [
            [(5, 4)],
            [(5, 4), (1, 2)],
            [(1, 2), (5, 4), (8, 9)],
            [(1, 10), (5, 4)],
        ]
        for intervals in cases:
            with self.subTest(intervals=intervals):
                original = intervals.copy()
                with self.assertRaises(ValueError):
                    union(intervals)
                self.assertEqual(intervals, original)


if __name__ == "__main__":
    unittest.main()
