import unittest

from solution import union, union_legacy


class UnionTests(unittest.TestCase):
    def test_merge_and_sort_without_mutating_input(self) -> None:
        intervals = [(8, 10), (2, 4), (1, 3), (4, 6), (2, 2), (8, 10)]
        original = intervals.copy()
        for merge in (union, union_legacy):
            with self.subTest(function=merge.__name__):
                result = merge(intervals)
                self.assertEqual(result, [(1, 6), (8, 10)])
                self.assertIsInstance(result, list)
                self.assertTrue(all(isinstance(interval, tuple) for interval in result))
                self.assertIsNot(result, intervals)
                self.assertEqual(intervals, original)

    def test_empty_and_point_intervals(self) -> None:
        for merge in (union, union_legacy):
            with self.subTest(function=merge.__name__):
                empty: list[tuple[int, int]] = []
                result = merge(empty)
                self.assertEqual(result, [])
                self.assertIsNot(result, empty)
                self.assertEqual(merge([(3, 3), (-2, -2)]), [(-2, -2), (3, 3)])

    def test_reversed_interval_raises_without_mutating_input(self) -> None:
        intervals = [(5, 7), (3, 2), (0, 1)]
        original = intervals.copy()
        for merge in (union, union_legacy):
            with self.subTest(function=merge.__name__):
                with self.assertRaisesRegex(ValueError, '^reversed interval$'):
                    merge(intervals)
                self.assertEqual(intervals, original)


if __name__ == '__main__':
    unittest.main()
