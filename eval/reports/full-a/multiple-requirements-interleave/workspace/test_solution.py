import unittest

from solution import interleave


class InterleaveTests(unittest.TestCase):
    def test_equal_lengths_alternate_left_then_right(self) -> None:
        self.assertEqual(interleave([1, 2, 3], [4, 5, 6]), [1, 4, 2, 5, 3, 6])

    def test_longer_left_preserves_remainder_order(self) -> None:
        self.assertEqual(interleave([1, 2, 3, 4], [5, 6]), [1, 5, 2, 6, 3, 4])

    def test_longer_right_preserves_remainder_order(self) -> None:
        self.assertEqual(interleave([1, 2], [3, 4, 5, 6]), [1, 3, 2, 4, 5, 6])

    def test_empty_inputs(self) -> None:
        for left, right, expected in (
            ([], [], []),
            ([], [3, 1, 2], [3, 1, 2]),
            ([3, 1, 2], [], [3, 1, 2]),
        ):
            with self.subTest(left=left, right=right):
                result = interleave(left, right)
                self.assertEqual(result, expected)
                self.assertIsNot(result, left)
                self.assertIsNot(result, right)

    def test_preserves_values_and_does_not_mutate_inputs(self) -> None:
        left = [0, -2, -2, 9]
        right = [7, 0, -5]
        left_before = left.copy()
        right_before = right.copy()
        result = interleave(left, right)
        self.assertEqual(result, [0, 7, -2, 0, -2, -5, 9])
        self.assertEqual(left, left_before)
        self.assertEqual(right, right_before)
        result.append(100)
        self.assertEqual(left, left_before)
        self.assertEqual(right, right_before)

    def test_same_collection_as_both_inputs(self) -> None:
        values = [3, 1, 3]
        self.assertEqual(interleave(values, values), [3, 3, 1, 1, 3, 3])
        self.assertEqual(values, [3, 1, 3])


if __name__ == "__main__":
    unittest.main()
