"""Tests for the public partition API."""

import unittest

from solution import partition


class PartitionTests(unittest.TestCase):
    def test_mixed_values_preserve_order_duplicates_and_input(self) -> None:
        items = [-3, 2, 0, -1, 2, 0, 5, -3, -8, 1]
        original = items.copy()

        self.assertEqual(
            partition(items),
            ([-3, -1, -3, -8], [0, 0], [2, 2, 5, 1]),
        )
        self.assertEqual(items, original)

    def test_empty_input(self) -> None:
        items: list[int] = []

        self.assertEqual(partition(items), ([], [], []))
        self.assertEqual(items, [])

    def test_single_element_inputs_around_zero(self) -> None:
        cases = [
            ([-1], ([-1], [], [])),
            ([0], ([], [0], [])),
            ([1], ([], [], [1])),
        ]
        for items, expected in cases:
            with self.subTest(items=items):
                self.assertEqual(partition(items), expected)

    def test_large_magnitude_integers(self) -> None:
        magnitude = 10**100

        self.assertEqual(
            partition([magnitude, -magnitude, 0, -1, 1]),
            ([-magnitude, -1], [0], [magnitude, 1]),
        )


if __name__ == "__main__":
    unittest.main()
