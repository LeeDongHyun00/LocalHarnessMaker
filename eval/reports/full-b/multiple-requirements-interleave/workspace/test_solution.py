import unittest

from solution import interleave


class InterleaveTests(unittest.TestCase):
    def test_equal_lengths_alternate_left_then_right(self) -> None:
        self.assertEqual(
            interleave([1, 2, 3], [10, 20, 30]),
            [1, 10, 2, 20, 3, 30],
        )

    def test_longer_left_appends_remainder_in_order(self) -> None:
        self.assertEqual(interleave([3, 1, 4, 2], [9]), [3, 9, 1, 4, 2])

    def test_longer_right_appends_remainder_in_order(self) -> None:
        self.assertEqual(interleave([9], [3, 1, 4, 2]), [9, 3, 1, 4, 2])

    def test_empty_inputs_return_a_new_list(self) -> None:
        cases = [
            ([], [], []),
            ([], [3, 1, 2], [3, 1, 2]),
            ([3, 1, 2], [], [3, 1, 2]),
        ]
        for left, right, expected in cases:
            with self.subTest(left=left, right=right):
                result = interleave(left, right)
                self.assertEqual(result, expected)
                self.assertIsNot(result, left)
                self.assertIsNot(result, right)

    def test_preserves_duplicates_zero_and_negative_values(self) -> None:
        self.assertEqual(
            interleave([0, -2, -2], [-1, 0, -1]),
            [0, -1, -2, 0, -2, -1],
        )

    def test_inputs_are_unchanged_and_result_is_independent(self) -> None:
        left = [3, 0, -2, 3]
        right = [5, 0]
        original_left = left.copy()
        original_right = right.copy()

        result = interleave(left, right)

        self.assertEqual(result, [3, 5, 0, 0, -2, 3])
        self.assertEqual(left, original_left)
        self.assertEqual(right, original_right)
        result[0] = 99
        result.append(100)
        self.assertEqual(left, original_left)
        self.assertEqual(right, original_right)

    def test_same_collection_can_be_used_for_both_inputs(self) -> None:
        values = [3, 1, 2]
        self.assertEqual(interleave(values, values), [3, 3, 1, 1, 2, 2])
        self.assertEqual(values, [3, 1, 2])


if __name__ == "__main__":
    unittest.main()
