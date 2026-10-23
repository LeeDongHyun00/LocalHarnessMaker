import unittest

from solution import windows


class WindowsTests(unittest.TestCase):
    def test_overlapping_windows_have_exact_size(self) -> None:
        self.assertEqual(
            windows([1, 2, 3, 4, 5], 3),
            [[1, 2, 3], [2, 3, 4], [3, 4, 5]],
        )

    def test_unit_size_and_full_length(self) -> None:
        items = [3, 1, 2]
        self.assertEqual(windows(items, 1), [[3], [1], [2]])
        self.assertEqual(windows(items, 3), [[3, 1, 2]])

    def test_size_exceeding_length_returns_empty(self) -> None:
        self.assertEqual(windows([1, 2, 3], 4), [])

    def test_empty_input_returns_empty(self) -> None:
        for size in (1, 2, 10):
            with self.subTest(size=size):
                self.assertEqual(windows([], size), [])

    def test_nonpositive_size_raises_value_error(self) -> None:
        for items in ([], [3, 1, 2]):
            original = items.copy()
            for size in (0, -1, -5):
                with self.subTest(items=items, size=size):
                    with self.assertRaises(ValueError):
                        windows(items, size)
                    self.assertEqual(items, original)

    def test_preserves_input_values_and_collection_order(self) -> None:
        items = [8, -2, 8, 0, 3]
        original = items.copy()
        self.assertEqual(
            windows(items, 2),
            [[8, -2], [-2, 8], [8, 0], [0, 3]],
        )
        self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
