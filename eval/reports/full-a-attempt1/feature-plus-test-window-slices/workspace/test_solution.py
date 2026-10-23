"""Tests for the public windows API."""

import unittest

from solution import windows


class WindowsTests(unittest.TestCase):
    def test_overlapping_windows(self) -> None:
        self.assertEqual(windows([1, 2, 3, 4], 2), [[1, 2], [2, 3], [3, 4]])
        self.assertEqual(windows([2, 2, -1, 0], 3), [[2, 2, -1], [2, -1, 0]])

    def test_boundary_sizes(self) -> None:
        items = [1, 2, 3]
        self.assertEqual(windows(items, 1), [[1], [2], [3]])
        self.assertEqual(windows(items, 3), [[1, 2, 3]])
        self.assertEqual(windows(items, 4), [])
        self.assertEqual(windows([7], 1), [[7]])

    def test_empty_input(self) -> None:
        self.assertEqual(windows([], 1), [])
        self.assertEqual(windows([], 5), [])

    def test_nonpositive_sizes(self) -> None:
        for items in ([], [1, 2, 3]):
            for size in (0, -1, -5):
                with self.subTest(items=items, size=size):
                    with self.assertRaises(ValueError):
                        windows(items, size)

    def test_input_is_unchanged_and_windows_are_independent(self) -> None:
        items = [1, 2, 3]
        result = windows(items, 2)
        self.assertEqual(items, [1, 2, 3])
        result[0][1] = 99
        self.assertEqual(items, [1, 2, 3])
        self.assertEqual(result[1], [2, 3])


if __name__ == "__main__":
    unittest.main()
