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
                    for window in result:
                        self.assertIsInstance(window, list)

    def test_empty_input(self):
        for function in (windows, windows_legacy):
            with self.subTest(function=function.__name__):
                self.assertEqual(function([], 1), [])

    def test_nonpositive_size_preserves_error_and_input(self):
        for function in (windows, windows_legacy):
            for items in ([], [1, 2, 3]):
                for size in (0, -1, -5):
                    with self.subTest(function=function.__name__, items=items, size=size):
                        original = items.copy()
                        with self.assertRaises(ValueError) as caught:
                            function(items, size)
                        self.assertEqual(str(caught.exception), 'positive size required')
                        self.assertEqual(items, original)

    def test_input_is_unchanged_and_windows_are_independent(self):
        for function in (windows, windows_legacy):
            with self.subTest(function=function.__name__):
                items = [1, 2, 3, 4]
                result = function(items, 2)
                self.assertEqual(items, [1, 2, 3, 4])
                result[0][1] = 99
                self.assertEqual(items, [1, 2, 3, 4])
                self.assertEqual(result[1], [2, 3])


if __name__ == '__main__':
    unittest.main()
