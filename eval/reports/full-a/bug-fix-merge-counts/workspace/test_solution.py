import unittest

from solution import merge


class MergeTests(unittest.TestCase):
    def test_adds_counts_preserves_nonpositive_totals_and_inputs(self) -> None:
        left = {"shared": 3, "zero": 2, "negative": -4, "left": 0}
        right = {"shared": 5, "zero": -2, "negative": 1, "right": -3}
        left_before = left.copy()
        right_before = right.copy()

        result = merge(left, right)

        self.assertEqual(
            result,
            {"shared": 8, "zero": 0, "negative": -3, "left": 0, "right": -3},
        )
        self.assertEqual(left, left_before)
        self.assertEqual(right, right_before)
        self.assertIsNot(result, left)
        self.assertIsNot(result, right)


if __name__ == "__main__":
    unittest.main()
