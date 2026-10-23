import unittest

from solution import windows


class WindowsTests(unittest.TestCase):
    def test_overlapping_windows_leave_input_unchanged(self):
        items = [1, 2, 3, 4]
        self.assertEqual(windows(items, 2), [[1, 2], [2, 3], [3, 4]])
        self.assertEqual(items, [1, 2, 3, 4])

    def test_boundary_sizes(self):
        for items, size, expected in (
            ([1, 2], 1, [[1], [2]]),
            ([1, 2], 2, [[1, 2]]),
            ([1, 2], 3, []),
            ([], 1, []),
        ):
            with self.subTest(items=items, size=size):
                self.assertEqual(windows(items, size), expected)

    def test_nonpositive_sizes_raise_value_error(self):
        for items in ([], [1, 2]):
            for size in (0, -1):
                with self.subTest(items=items, size=size):
                    with self.assertRaises(ValueError):
                        windows(items, size)
