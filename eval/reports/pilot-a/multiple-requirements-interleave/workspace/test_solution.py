import unittest

from solution import interleave


class InterleaveTests(unittest.TestCase):
    def test_equal_lengths_alternate_left_then_right(self) -> None:
        self.assertEqual(interleave([3, 1, 2], [6, 4, 5]), [3, 6, 1, 4, 2, 5])

    def test_left_remainder_keeps_original_order(self) -> None:
        self.assertEqual(interleave([5, 0, -2, 5], [9]), [5, 9, 0, -2, 5])

    def test_right_remainder_keeps_original_order(self) -> None:
        self.assertEqual(interleave([9], [5, 0, -2, 5]), [9, 5, 0, -2, 5])

    def test_empty_inputs(self) -> None:
        for left, right, expected in [
            ([], [], []),
            ([], [3, 0, -1], [3, 0, -1]),
            ([3, 0, -1], [], [3, 0, -1]),
        ]:
            with self.subTest(left=left, right=right):
                self.assertEqual(interleave(left, right), expected)

    def test_inputs_are_unchanged_and_result_is_independent(self) -> None:
        for left, right in [([3, 0, 3], [-1]), ([], [2]), ([2], [])]:
            with self.subTest(left=left, right=right):
                original_left = left.copy()
                original_right = right.copy()
                result = interleave(left, right)
                self.assertEqual(left, original_left)
                self.assertEqual(right, original_right)
                self.assertIsNot(result, left)
                self.assertIsNot(result, right)
                result.append(100)
                self.assertEqual(left, original_left)
                self.assertEqual(right, original_right)

    def test_same_collection_as_both_inputs(self) -> None:
        values = [2, 0, -3]
        self.assertEqual(interleave(values, values), [2, 2, 0, 0, -3, -3])
        self.assertEqual(values, [2, 0, -3])


if __name__ == "__main__":
    unittest.main()
