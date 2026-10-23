import unittest

from solution import interleave


class InterleaveTests(unittest.TestCase):
    def test_alternates_and_preserves_remainders_without_mutation(self) -> None:
        cases = [
            ([1, 3], [2, 4], [1, 2, 3, 4]),
            ([1, 3, 5, 7], [2], [1, 2, 3, 5, 7]),
            ([1], [2, 4, 6, 8], [1, 2, 4, 6, 8]),
            ([], [2, 4], [2, 4]),
            ([1, 3], [], [1, 3]),
            ([], [], []),
        ]
        for left, right, expected in cases:
            with self.subTest(left=left, right=right):
                original_left, original_right = left.copy(), right.copy()
                self.assertEqual(interleave(left, right), expected)
                self.assertEqual(left, original_left)
                self.assertEqual(right, original_right)
