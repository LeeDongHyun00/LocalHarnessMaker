import unittest

from solution import windows


class WindowsTests(unittest.TestCase):
    def test_overlapping_complete_windows_preserve_input(self) -> None:
        items = [1, 2, 3, 4, 5]
        self.assertEqual(windows(items, 3), [[1, 2, 3], [2, 3, 4], [3, 4, 5]])
        self.assertEqual(items, [1, 2, 3, 4, 5])

    def test_boundary_sizes(self) -> None:
        self.assertEqual(windows([1, 2], 1), [[1], [2]])
        self.assertEqual(windows([1, 2], 2), [[1, 2]])
        self.assertEqual(windows([1, 2], 3), [])
        self.assertEqual(windows([], 1), [])

    def test_nonpositive_sizes_raise(self) -> None:
        for size in (0, -1):
            for items in ([], [1, 2]):
                with self.subTest(size=size, items=items):
                    with self.assertRaises(ValueError):
                        windows(items, size)
