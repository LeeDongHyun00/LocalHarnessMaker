import unittest

from solution import windows, windows_legacy


class WindowsTests(unittest.TestCase):
    def test_contiguous_windows(self):
        for function in (windows, windows_legacy):
            with self.subTest(function=function.__name__):
                self.assertEqual(
                    function([1, 2, 3, 4], 2),
                    [[1, 2], [2, 3], [3, 4]],
                )

    def test_boundary_sizes(self):
        cases = [
            ([], 1, []),
            ([1, 2, 3], 1, [[1], [2], [3]]),
            ([1, 2, 3], 3, [[1, 2, 3]]),
            ([1, 2, 3], 4, []),
        ]
        for function in (windows, windows_legacy):
            for items, size, expected in cases:
                with self.subTest(
                    function=function.__name__, items=items, size=size
                ):
                    original = items.copy()
                    self.assertEqual(function(items, size), expected)
                    self.assertEqual(items, original)

    def test_nonpositive_size_preserves_error_and_input(self):
        for function in (windows, windows_legacy):
            for items in ([], [1, 2, 3]):
                for size in (0, -1, -5):
                    with self.subTest(
                        function=function.__name__, items=items, size=size
                    ):
                        original = items.copy()
                        with self.assertRaisesRegex(
                            ValueError, '^positive size required$'
                        ):
                            function(items, size)
                        self.assertEqual(items, original)

    def test_results_are_independent_lists_and_preserve_input(self):
        for function in (windows, windows_legacy):
            with self.subTest(function=function.__name__):
                items = [1, 2, 3, 4]
                result = function(items, 2)
                self.assertIs(type(result), list)
                for window in result:
                    self.assertIs(type(window), list)
                self.assertEqual(items, [1, 2, 3, 4])

                result[0][1] = 99
                result[0].append(100)
                self.assertEqual(items, [1, 2, 3, 4])
                self.assertEqual(result[1:], [[2, 3], [3, 4]])


if __name__ == '__main__':
    unittest.main()
