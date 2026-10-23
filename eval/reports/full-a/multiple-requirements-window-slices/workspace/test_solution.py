import unittest

from solution import windows


class WindowsTests(unittest.TestCase):
    def test_overlapping_windows_preserve_values_and_order(self):
        items = [4, -2, 4, 0, 9]
        self.assertEqual(windows(items, 3), [[4, -2, 4], [-2, 4, 0], [4, 0, 9]])
        self.assertEqual(items, [4, -2, 4, 0, 9])

    def test_only_complete_windows_are_returned(self):
        self.assertEqual(windows([1, 2, 3, 4, 5], 2),
                         [[1, 2], [2, 3], [3, 4], [4, 5]])

    def test_size_one_and_size_equal_to_length(self):
        self.assertEqual(windows([3, 1, 2], 1), [[3], [1], [2]])
        self.assertEqual(windows([3, 1, 2], 3), [[3, 1, 2]])

    def test_oversized_windows_and_empty_input(self):
        self.assertEqual(windows([1, 2], 3), [])
        self.assertEqual(windows([], 1), [])

    def test_nonpositive_sizes_raise_without_mutating_input(self):
        for items in ([], [3, 1, 2]):
            for size in (0, -1, -5):
                with self.subTest(items=items, size=size):
                    original = items.copy()
                    with self.assertRaises(ValueError):
                        windows(items, size)
                    self.assertEqual(items, original)

    def test_windows_are_independent_lists(self):
        items = [1, 2, 3]
        result = windows(items, 2)
        result[0][1] = 99
        self.assertEqual(items, [1, 2, 3])
        self.assertEqual(result[1], [2, 3])


if __name__ == "__main__":
    unittest.main()
