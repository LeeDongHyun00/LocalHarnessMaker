import inspect
import unittest

from solution import windows


class WindowsTests(unittest.TestCase):
    def test_signature_is_preserved(self) -> None:
        self.assertEqual(
            str(inspect.signature(windows)),
            "(items: list[int], size: int) -> list[list[int]]",
        )

    def test_all_small_lengths_and_sizes(self) -> None:
        for length in range(6):
            for size in range(-2, length + 3):
                with self.subTest(length=length, size=size):
                    items = list(range(length))
                    original = items.copy()
                    if size <= 0:
                        with self.assertRaises(ValueError):
                            windows(items, size)
                    else:
                        result = windows(items, size)
                        expected = [
                            list(range(start, start + size))
                            for start in range(length)
                            if start + size <= length
                        ]
                        self.assertEqual(result, expected)
                        self.assertTrue(all(len(window) == size for window in result))
                    self.assertEqual(items, original)

    def test_contiguous_windows_do_not_mutate_input(self) -> None:
        items = [1, 2, 3, 4]
        self.assertEqual(windows(items, 2), [[1, 2], [2, 3], [3, 4]])
        self.assertEqual(items, [1, 2, 3, 4])

    def test_boundary_sizes(self) -> None:
        items = [1, 2, 3]
        self.assertEqual(windows(items, 1), [[1], [2], [3]])
        self.assertEqual(windows(items, 3), [[1, 2, 3]])
        self.assertEqual(windows(items, 4), [])
        self.assertEqual(windows([], 1), [])
        self.assertEqual(items, [1, 2, 3])

    def test_nonpositive_sizes_raise(self) -> None:
        for items in ([], [1, 2, 3]):
            for size in (0, -1):
                with self.subTest(items=items, size=size):
                    original = items.copy()
                    with self.assertRaises(ValueError):
                        windows(items, size)
                    self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
