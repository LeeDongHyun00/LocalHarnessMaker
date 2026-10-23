"""Tests for the public interleave API."""

import unittest

from solution import interleave


class InterleaveTests(unittest.TestCase):
    def test_equal_length_inputs(self) -> None:
        self.assertEqual(interleave([1, 2, 3], [4, 5, 6]), [1, 4, 2, 5, 3, 6])

    def test_unequal_lengths(self) -> None:
        self.assertEqual(interleave([1, 2, 3], [4]), [1, 4, 2, 3])
        self.assertEqual(interleave([1], [2, 3, 4]), [1, 2, 3, 4])

    def test_empty_inputs(self) -> None:
        self.assertEqual(interleave([], []), [])
        self.assertEqual(interleave([], [1, 2]), [1, 2])
        self.assertEqual(interleave([1, 2], []), [1, 2])

    def test_singletons_and_integer_values(self) -> None:
        self.assertEqual(interleave([0], [-1]), [0, -1])
        self.assertEqual(interleave([-2, -2], [0, 0]), [-2, 0, -2, 0])

    def test_inputs_are_not_mutated(self) -> None:
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


if __name__ == "__main__":
    unittest.main()
