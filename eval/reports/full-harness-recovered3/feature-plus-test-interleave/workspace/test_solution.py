"""Tests for the public interleave API."""

import unittest

from solution import interleave


class InterleaveTests(unittest.TestCase):
    def test_equal_lengths(self) -> None:
        self.assertEqual(interleave([1, 2, 3], [4, 5, 6]), [1, 4, 2, 5, 3, 6])

    def test_unequal_lengths(self) -> None:
        self.assertEqual(interleave([1, 2, 3], [4]), [1, 4, 2, 3])
        self.assertEqual(interleave([1], [2, 3, 4]), [1, 2, 3, 4])

    def test_empty_inputs(self) -> None:
        self.assertEqual(interleave([], []), [])
        self.assertEqual(interleave([], [1, 2]), [1, 2])
        self.assertEqual(interleave([1, 2], []), [1, 2])

    def test_single_items_and_repeated_values(self) -> None:
        self.assertEqual(interleave([0], [-1]), [0, -1])
        self.assertEqual(interleave([2, 2], [2, 2]), [2, 2, 2, 2])

    def test_inputs_are_preserved_and_result_is_independent(self) -> None:
        left = [1, 2, 3]
        right = [4, 5]
        result = interleave(left, right)
        self.assertEqual(left, [1, 2, 3])
        self.assertEqual(right, [4, 5])
        self.assertIsNot(result, left)
        self.assertIsNot(result, right)
        result.append(6)
        self.assertEqual(left, [1, 2, 3])
        self.assertEqual(right, [4, 5])

    def test_same_list_as_both_inputs(self) -> None:
        values = [1, 2]
        self.assertEqual(interleave(values, values), [1, 1, 2, 2])
        self.assertEqual(values, [1, 2])


if __name__ == "__main__":
    unittest.main()
