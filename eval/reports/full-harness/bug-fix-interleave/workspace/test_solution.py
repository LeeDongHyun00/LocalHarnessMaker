import unittest

from solution import interleave


class InterleaveTests(unittest.TestCase):
    def test_interleave_preserves_remainders_and_inputs(self) -> None:
        cases = [
            ([1, 2, 3], [10], [1, 10, 2, 3]),
            ([1], [10, 20, 30], [1, 10, 20, 30]),
            ([1, 2], [10, 20], [1, 10, 2, 20]),
            ([], [10, 20], [10, 20]),
            ([1, 2], [], [1, 2]),
            ([], [], []),
        ]
        for left, right, expected in cases:
            with self.subTest(left=left, right=right):
                original_left = left.copy()
                original_right = right.copy()
                self.assertEqual(interleave(left, right), expected)
                self.assertEqual(left, original_left)
                self.assertEqual(right, original_right)


if __name__ == "__main__":
    unittest.main()
