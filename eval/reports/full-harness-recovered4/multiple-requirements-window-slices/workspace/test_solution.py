import unittest

from solution import windows


class WindowsTests(unittest.TestCase):
    def test_overlapping_windows_preserve_values_and_order(self):
        items = [4, -2, 4, 0, 9]
        original = items.copy()
        self.assertEqual(windows(items, 3), [[4, -2, 4], [-2, 4, 0], [4, 0, 9]])
        self.assertEqual(items, original)

    def test_size_one_and_full_length(self):
        self.assertEqual(windows([3, 1, 2], 1), [[3], [1], [2]])
        self.assertEqual(windows([3, 1, 2], 3), [[3, 1, 2]])

    def test_oversized_and_empty_inputs(self):
        self.assertEqual(windows([1, 2], 3), [])
        self.assertEqual(windows([], 1), [])

    def test_nonpositive_sizes_raise(self):
        for items in ([], [1, 2, 3]):
            for size in (0, -1, -3):
                with self.subTest(items=items, size=size):
                    with self.assertRaises(ValueError):
                        windows(items, size)

    def test_returned_windows_are_independent_of_input_and_each_other(self):
        items = [1, 2, 3]
        result = windows(items, 2)
        result[0][1] = 99
        self.assertEqual(items, [1, 2, 3])
        self.assertEqual(result[1], [2, 3])


if __name__ == "__main__":
    unittest.main()
