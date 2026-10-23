import unittest

from solution import interleave


class InterleaveTests(unittest.TestCase):
    def test_alternates_left_then_right(self):
        self.assertEqual(interleave([1, 2, 3], [4, 5, 6]), [1, 4, 2, 5, 3, 6])

    def test_preserves_longer_input_remainder_order(self):
        cases = [
            ([1, 2, 3, 4], [5], [1, 5, 2, 3, 4]),
            ([1], [2, 3, 4, 5], [1, 2, 3, 4, 5]),
        ]
        for left, right, expected in cases:
            with self.subTest(left=left, right=right):
                self.assertEqual(interleave(left, right), expected)

    def test_accepts_empty_inputs(self):
        for left, right in [([], []), ([], [3, 1, 2]), ([3, 1, 2], [])]:
            with self.subTest(left=left, right=right):
                result = interleave(left, right)
                self.assertEqual(result, left + right)
                self.assertIsNot(result, left)
                self.assertIsNot(result, right)

    def test_preserves_values_and_does_not_mutate_inputs(self):
        left = [0, -2, -2, 7]
        right = [5, 0]
        left_before, right_before = left.copy(), right.copy()
        result = interleave(left, right)
        self.assertEqual(result, [0, 5, -2, 0, -2, 7])
        self.assertEqual(left, left_before)
        self.assertEqual(right, right_before)
        result.append(99)
        self.assertEqual(left, left_before)
        self.assertEqual(right, right_before)

    def test_accepts_same_collection_for_both_inputs(self):
        values = [3, 1, 2]
        self.assertEqual(interleave(values, values), [3, 3, 1, 1, 2, 2])
        self.assertEqual(values, [3, 1, 2])


if __name__ == "__main__":
    unittest.main()
