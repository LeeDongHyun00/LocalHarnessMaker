"""Tests for the public interleave API."""

import unittest

from solution import interleave


class InterleaveTests(unittest.TestCase):
    def test_equal_length_inputs(self) -> None:
        self.assertEqual(interleave([1, 3, 5], [2, 4, 6]), [1, 2, 3, 4, 5, 6])

    def test_longer_left_input(self) -> None:
        self.assertEqual(interleave([1, 3, 5, 7], [2, 4]), [1, 2, 3, 4, 5, 7])

    def test_longer_right_input(self) -> None:
        self.assertEqual(interleave([1, 3], [2, 4, 6, 8]), [1, 2, 3, 4, 6, 8])

    def test_empty_inputs(self) -> None:
        cases = [
            ([], [], []),
            ([], [2, 4, 6], [2, 4, 6]),
            ([1, 3, 5], [], [1, 3, 5]),
            ([], [0], [0]),
            ([0], [], [0]),
        ]
        for left, right, expected in cases:
            with self.subTest(left=left, right=right):
                self.assertEqual(interleave(left, right), expected)

    def test_single_item_inputs(self) -> None:
        self.assertEqual(interleave([1], [2]), [1, 2])
        self.assertEqual(interleave([1], [2, 3]), [1, 2, 3])
        self.assertEqual(interleave([1, 3], [2]), [1, 2, 3])

    def test_negative_zero_and_duplicate_values(self) -> None:
        self.assertEqual(interleave([-2, 0, -2], [0, -1]), [-2, 0, 0, -1, -2])

    def test_inputs_are_not_mutated(self) -> None:
        cases = [([1, 3, 5], [2]), ([1], [2, 4, 6]), ([], [2]), ([1], [])]
        for left, right in cases:
            with self.subTest(left=left, right=right):
                original_left = left.copy()
                original_right = right.copy()
                interleave(left, right)
                self.assertEqual(left, original_left)
                self.assertEqual(right, original_right)

    def test_same_list_as_both_inputs(self) -> None:
        values = [1, 2, 3]
        self.assertEqual(interleave(values, values), [1, 1, 2, 2, 3, 3])
        self.assertEqual(values, [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
