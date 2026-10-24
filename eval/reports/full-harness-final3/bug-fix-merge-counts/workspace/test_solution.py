import unittest

from solution import merge


class MergeTests(unittest.TestCase):
    def test_adds_counts_preserves_all_keys_and_leaves_inputs_unchanged(self):
        left = {"shared": 2, "zero": 3, "negative": -4, "left": 0}
        right = {"shared": 5, "zero": -3, "negative": 1, "right": -2}
        original_left = left.copy()
        original_right = right.copy()

        result = merge(left, right)

        self.assertEqual(
            result,
            {"shared": 7, "zero": 0, "negative": -3, "left": 0, "right": -2},
        )
        self.assertEqual(left, original_left)
        self.assertEqual(right, original_right)
        self.assertIsNot(result, left)
        self.assertIsNot(result, right)


if __name__ == "__main__":
    unittest.main()
