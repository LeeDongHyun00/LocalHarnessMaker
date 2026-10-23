import unittest

from solution import merge


class MergeTests(unittest.TestCase):
    def test_adds_shared_counts_and_preserves_inputs(self) -> None:
        left = {"shared": 2, "zero": 3, "negative": -4, "left_only": 0}
        right = {"shared": 5, "zero": -3, "negative": 1, "right_only": -2}
        original_left = left.copy()
        original_right = right.copy()

        result = merge(left, right)

        self.assertEqual(
            result,
            {"shared": 7, "zero": 0, "negative": -3, "left_only": 0, "right_only": -2},
        )
        self.assertEqual(left, original_left)
        self.assertEqual(right, original_right)

    def test_empty_inputs(self) -> None:
        for left, right in (({}, {}), ({"zero": 0}, {}), ({}, {"negative": -1})):
            with self.subTest(left=left, right=right):
                self.assertEqual(merge(left, right), left | right)


if __name__ == "__main__":
    unittest.main()
