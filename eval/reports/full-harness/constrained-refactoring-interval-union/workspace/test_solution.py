import unittest

from solution import union, union_legacy


class UnionTests(unittest.TestCase):
    def test_merge_and_sort_without_mutating_input(self):
        for merge in (union, union_legacy):
            with self.subTest(api=merge.__name__):
                intervals = [(10, 12), (3, 5), (1, 3), (2, 4), (8, 8), (1, 3)]
                original = intervals.copy()
                result = merge(intervals)
                self.assertIsInstance(result, list)
                self.assertEqual(result, [(1, 5), (8, 8), (10, 12)])
                self.assertTrue(all(isinstance(item, tuple) for item in result))
                self.assertEqual(intervals, original)
                self.assertIsNot(result, intervals)

    def test_empty_input(self):
        for merge in (union, union_legacy):
            with self.subTest(api=merge.__name__):
                intervals = []
                result = merge(intervals)
                self.assertEqual(result, [])
                self.assertIsNot(result, intervals)
                self.assertEqual(intervals, [])

    def test_reversed_interval_raises_without_mutating_input(self):
        for merge in (union, union_legacy):
            with self.subTest(api=merge.__name__):
                intervals = [(9, 10), (4, 2), (1, 5)]
                original = intervals.copy()
                with self.assertRaisesRegex(ValueError, '^reversed interval$'):
                    merge(intervals)
                self.assertEqual(intervals, original)


if __name__ == '__main__':
    unittest.main()
