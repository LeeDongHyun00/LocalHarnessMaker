import unittest

from solution import interleave


class InterleaveTests(unittest.TestCase):
    def test_interleave_preserves_all_items_and_inputs(self) -> None:
        cases = [
            ([1, 3], [2, 4], [1, 2, 3, 4]),
            ([1, 3, 5, 7], [2, 4], [1, 2, 3, 4, 5, 7]),
            ([1], [2, 3, 4], [1, 2, 3, 4]),
            ([], [2, 4], [2, 4]),
            ([1, 3], [], [1, 3]),
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
