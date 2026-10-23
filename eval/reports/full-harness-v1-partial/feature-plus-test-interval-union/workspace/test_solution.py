import unittest

from solution import union


class UnionTests(unittest.TestCase):
    def test_merges_overlapping_intervals_and_sorts(self) -> None:
        self.assertEqual(
            union([(8, 10), (2, 6), (1, 3), (15, 18)]),
            [(1, 6), (8, 10), (15, 18)],
        )

    def test_touching_intervals_and_point_boundaries(self) -> None:
        self.assertEqual(
            union([(3, 3), (1, 2), (2, 3), (-2, 1), (5, 5)]),
            [(-2, 3), (5, 5)],
        )
        self.assertEqual(union([(1, 2), (3, 4)]), [(1, 2), (3, 4)])

    def test_nested_and_duplicate_intervals(self) -> None:
        self.assertEqual(union([(1, 10), (2, 3), (1, 10)]), [(1, 10)])

    def test_empty_and_single_interval(self) -> None:
        self.assertEqual(union([]), [])
        self.assertEqual(union([(4, 4)]), [(4, 4)])

    def test_reversed_interval_raises_value_error(self) -> None:
        for intervals in ([(3, 2)], [(0, 10), (5, 4)], [(2, -1)]):
            with self.subTest(intervals=intervals):
                original = intervals.copy()
                with self.assertRaises(ValueError):
                    union(intervals)
                self.assertEqual(intervals, original)

    def test_does_not_mutate_or_return_input(self) -> None:
        intervals = [(8, 10), (1, 3), (3, 5)]
        original = intervals.copy()
        result = union(intervals)
        self.assertEqual(intervals, original)
        self.assertEqual(result, [(1, 5), (8, 10)])
        self.assertIsNot(result, intervals)
        result.append((20, 30))
        self.assertEqual(intervals, original)


if __name__ == "__main__":
    unittest.main()
