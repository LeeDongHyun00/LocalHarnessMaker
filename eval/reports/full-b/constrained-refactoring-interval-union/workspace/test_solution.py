import unittest

from solution import union, union_legacy


class UnionTests(unittest.TestCase):
    def test_merges_unsorted_overlapping_touching_and_nested_intervals(self):
        intervals = [(10, 12), (3, 5), (1, 3), (2, 4), (8, 10), (3, 5)]
        original = intervals.copy()

        for merge in (union, union_legacy):
            with self.subTest(function=merge.__name__):
                result = merge(intervals)
                self.assertEqual(result, [(1, 5), (8, 12)])
                self.assertIsNot(result, intervals)
                self.assertEqual(intervals, original)

    def test_handles_negative_endpoints_and_single_point_intervals(self):
        intervals = [(4, 4), (-2, 0), (-5, -2), (1, 1), (4, 4)]

        for merge in (union, union_legacy):
            with self.subTest(function=merge.__name__):
                self.assertEqual(merge(intervals), [(-5, 0), (1, 1), (4, 4)])

    def test_empty_input_returns_a_new_empty_list(self):
        for merge in (union, union_legacy):
            with self.subTest(function=merge.__name__):
                intervals: list[tuple[int, int]] = []
                result = merge(intervals)
                self.assertEqual(result, [])
                self.assertIsNot(result, intervals)
                self.assertEqual(intervals, [])

    def test_reversed_interval_raises_without_mutating_input(self):
        for merge in (union, union_legacy):
            for intervals in ([(5, 2)], [(8, 10), (5, 2), (1, 4)]):
                with self.subTest(function=merge.__name__, intervals=intervals):
                    original = intervals.copy()
                    with self.assertRaisesRegex(ValueError, "^reversed interval$"):
                        merge(intervals)
                    self.assertEqual(intervals, original)

    def test_result_can_be_changed_without_affecting_input(self):
        for merge in (union, union_legacy):
            with self.subTest(function=merge.__name__):
                intervals = [(3, 5), (1, 2)]
                result = merge(intervals)
                result[0] = (0, 10)
                result.append((20, 30))
                self.assertEqual(intervals, [(3, 5), (1, 2)])


if __name__ == "__main__":
    unittest.main()
