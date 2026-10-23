import unittest

from solution import union, union_legacy


class UnionTests(unittest.TestCase):
    def test_merges_and_sorts_without_mutating_input(self) -> None:
        for merge in (union, union_legacy):
            with self.subTest(function=merge.__name__):
                intervals = [(8, 9), (3, 5), (1, 3), (2, 2), (8, 9), (-4, -2)]
                original = intervals.copy()
                result = merge(intervals)
                self.assertEqual(result, [(-4, -2), (1, 5), (8, 9)])
                self.assertEqual(intervals, original)
                self.assertIsInstance(result, list)
                self.assertTrue(all(isinstance(interval, tuple) for interval in result))
                self.assertIsNot(result, intervals)

    def test_empty_and_singleton_inputs(self) -> None:
        for merge in (union, union_legacy):
            for intervals in ([], [(2, 2)], [(1, 4)]):
                with self.subTest(function=merge.__name__, intervals=intervals):
                    result = merge(intervals)
                    self.assertEqual(result, intervals)
                    self.assertIsNot(result, intervals)

    def test_reversed_intervals_raise_without_mutating_input(self) -> None:
        for merge in (union, union_legacy):
            for intervals in ([(4, 3)], [(0, 10), (4, 3)], [(8, 9), (4, 3)]):
                with self.subTest(function=merge.__name__, intervals=intervals):
                    original = intervals.copy()
                    with self.assertRaisesRegex(ValueError, '^reversed interval$'):
                        merge(intervals)
                    self.assertEqual(intervals, original)


if __name__ == '__main__':
    unittest.main()
