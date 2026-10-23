import unittest

from solution import windows, windows_legacy


class WindowsTests(unittest.TestCase):
    def test_contiguous_windows_and_boundaries(self) -> None:
        cases = [
            ([1, 2, 3, 4], 2, [[1, 2], [2, 3], [3, 4]]),
            ([1, 2, 3], 1, [[1], [2], [3]]),
            ([1, 2, 3], 3, [[1, 2, 3]]),
            ([1, 2, 3], 4, []),
            ([], 1, []),
        ]
        for function in (windows, windows_legacy):
            for items, size, expected in cases:
                with self.subTest(function=function.__name__, items=items, size=size):
                    result = function(items, size)
                    self.assertEqual(result, expected)
                    self.assertIsInstance(result, list)
                    for window in result:
                        self.assertIsInstance(window, list)

    def test_nonpositive_sizes_raise_original_error(self) -> None:
        for function in (windows, windows_legacy):
            for items in ([], [1, 2, 3]):
                for size in (0, -1, -10):
                    with self.subTest(function=function.__name__, items=items, size=size):
                        original = items.copy()
                        with self.assertRaisesRegex(ValueError, '^positive size required$'):
                            function(items, size)
                        self.assertEqual(items, original)

    def test_input_is_unchanged_and_windows_are_independent(self) -> None:
        for function in (windows, windows_legacy):
            with self.subTest(function=function.__name__):
                items = [1, 2, 3]
                result = function(items, 2)
                self.assertEqual(items, [1, 2, 3])
                result[0][1] = 99
                self.assertEqual(items, [1, 2, 3])
                self.assertEqual(result[1], [2, 3])
                items[2] = 42
                self.assertEqual(result[1], [2, 3])


if __name__ == '__main__':
    unittest.main()
