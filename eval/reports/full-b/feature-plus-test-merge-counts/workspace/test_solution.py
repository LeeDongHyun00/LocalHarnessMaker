"""Tests for the public merge API."""

import unittest

from solution import merge


class MergeTests(unittest.TestCase):
    def test_shared_and_distinct_keys(self) -> None:
        self.assertEqual(
            merge({"apple": 2, "pear": 3}, {"apple": 4, "orange": 5}),
            {"apple": 6, "pear": 3, "orange": 5},
        )

    def test_disjoint_keys(self) -> None:
        self.assertEqual(merge({"left": 2}, {"right": 7}), {"left": 2, "right": 7})

    def test_preserves_zero_and_negative_totals(self) -> None:
        left = {"cancel": 5, "negative": -4, "left_zero": 0, "left_negative": -2}
        right = {"cancel": -5, "negative": 1, "right_zero": 0, "right_negative": -3}

        self.assertEqual(
            merge(left, right),
            {
                "cancel": 0,
                "negative": -3,
                "left_zero": 0,
                "left_negative": -2,
                "right_zero": 0,
                "right_negative": -3,
            },
        )

    def test_empty_inputs(self) -> None:
        cases = [
            ({}, {}, {}),
            (
                {"positive": 2, "zero": 0, "negative": -1},
                {},
                {"positive": 2, "zero": 0, "negative": -1},
            ),
            (
                {},
                {"positive": 2, "zero": 0, "negative": -1},
                {"positive": 2, "zero": 0, "negative": -1},
            ),
        ]
        for left, right, expected in cases:
            with self.subTest(left=left, right=right):
                original_left = left.copy()
                original_right = right.copy()
                self.assertEqual(merge(left, right), expected)
                self.assertEqual(left, original_left)
                self.assertEqual(right, original_right)

    def test_does_not_change_inputs(self) -> None:
        left = {"shared": 3, "left_only": -2}
        right = {"shared": -3, "right_only": 0}
        original_left = left.copy()
        original_right = right.copy()

        result = merge(left, right)

        self.assertEqual(result, {"shared": 0, "left_only": -2, "right_only": 0})
        self.assertEqual(left, original_left)
        self.assertEqual(right, original_right)

    def test_same_dictionary_as_both_inputs(self) -> None:
        counts = {"positive": 3, "zero": 0, "negative": -2}
        original = counts.copy()

        self.assertEqual(
            merge(counts, counts), {"positive": 6, "zero": 0, "negative": -4}
        )
        self.assertEqual(counts, original)

    def test_large_integer_counts(self) -> None:
        large = 10**100
        self.assertEqual(
            merge(
                {"positive": large, "negative": -large},
                {"positive": large, "negative": -large},
            ),
            {"positive": 2 * large, "negative": -2 * large},
        )


if __name__ == "__main__":
    unittest.main()
