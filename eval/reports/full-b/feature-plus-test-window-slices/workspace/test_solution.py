"""Tests for the public windows API."""

import unittest

from solution import windows


class WindowsTests(unittest.TestCase):
    def test_overlapping_windows(self) -> None:
        self.assertEqual(
            windows([1, 2, 3, 4, 5], 3),
            [[1, 2, 3], [2, 3, 4], [3, 4, 5]],
        )
        self.assertEqual(
            windows([-2, 0, -2, 3], 2),
            [[-2, 0], [0, -2], [-2, 3]],
        )

    def test_boundary_sizes(self) -> None:
        items = [1, 2, 3]
        cases = (
            (1, [[1], [2], [3]]),
            (3, [[1, 2, 3]]),
            (4, []),
            (10, []),
        )
        for size, expected in cases:
            with self.subTest(size=size):
                self.assertEqual(windows(items, size), expected)
        self.assertEqual(windows([7], 1), [[7]])
        self.assertEqual(windows([7], 2), [])

    def test_empty_input(self) -> None:
        for size in (1, 2, 10):
            with self.subTest(size=size):
                self.assertEqual(windows([], size), [])

    def test_nonpositive_sizes_raise_value_error(self) -> None:
        for items in ([], [1, 2, 3]):
            for size in (0, -1, -10):
                with self.subTest(items=items, size=size):
                    with self.assertRaises(ValueError):
                        windows(items, size)

    def test_input_is_not_mutated(self) -> None:
        for size in (1, 2, 3, 4, 0, -1):
            with self.subTest(size=size):
                items = [3, 1, 2]
                original = items.copy()
                if size <= 0:
                    with self.assertRaises(ValueError):
                        windows(items, size)
                else:
                    windows(items, size)
                self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
