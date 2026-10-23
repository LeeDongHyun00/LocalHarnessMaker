import unittest

from solution import windows, windows_legacy


class WindowsTests(unittest.TestCase):
    def test_contiguous_windows(self):
        for function in (windows, windows_legacy):
            for size, expected in (
                (1, [[1], [2], [3], [4]]),
                (2, [[1, 2], [2, 3], [3, 4]]),
                (4, [[1, 2, 3, 4]]),
                (5, []),
            ):
                with self.subTest(function=function.__name__, size=size):
                    result = function([1, 2, 3, 4], size)
                    self.assertEqual(result, expected)
                    self.assertIsInstance(result, list)
                    self.assertTrue(all(isinstance(window, list) for window in result))

    def test_empty_input(self):
        for function in (windows, windows_legacy):
            with self.subTest(function=function.__name__):
                self.assertEqual(function([], 1), [])

    def test_nonpositive_size(self):
        for function in (windows, windows_legacy):
            for items in ([], [1, 2, 3]):
                for size in (0, -1, -5):
                    with self.subTest(function=function.__name__, items=items, size=size):
                        with self.assertRaisesRegex(ValueError, '^positive size required$'):
                            function(items, size)

    def test_input_is_unchanged_and_windows_are_independent(self):
        for function in (windows, windows_legacy):
            with self.subTest(function=function.__name__):
                items = [1, 2, 3]
                result = function(items, 2)
                self.assertEqual(items, [1, 2, 3])
                result[0][1] = 99
                self.assertEqual(items, [1, 2, 3])
                self.assertEqual(result[1], [2, 3])
                full_window = function(items, len(items))
                self.assertIsNot(full_window[0], items)


if __name__ == '__main__':
    unittest.main()
