"""Regression tests for the public merge API."""

import unittest

from solution import merge


class MergeTests(unittest.TestCase):
    def test_union_and_shared_counts(self) -> None:
        self.assertEqual(
            merge({"left": 2, "shared": 3}, {"shared": 4, "right": 5}),
            {"left": 2, "shared": 7, "right": 5},
        )

    def test_zero_and_negative_counts_are_preserved(self) -> None:
        self.assertEqual(
            merge(
                {"cancel": 3, "negative": -4, "left_zero": 0, "left_only": -2},
                {"cancel": -3, "negative": 1, "right_zero": 0, "right_only": -5},
            ),
            {
                "cancel": 0,
                "negative": -3,
                "left_zero": 0,
                "left_only": -2,
                "right_zero": 0,
                "right_only": -5,
            },
        )

    def test_inputs_and_their_order_are_unchanged(self) -> None:
        left = {"z": 1, "a": 2}
        right = {"b": 3, "a": 4, "c": 5, "z": 6}
        left_items = list(left.items())
        right_items = list(right.items())

        result = merge(left, right)

        self.assertEqual(list(result.items()), [("z", 7), ("a", 6), ("b", 3), ("c", 5)])
        self.assertEqual(list(left.items()), left_items)
        self.assertEqual(list(right.items()), right_items)
        self.assertIsNot(result, left)
        self.assertIsNot(result, right)
        result["a"] = 100
        self.assertEqual(list(left.items()), left_items)
        self.assertEqual(list(right.items()), right_items)

    def test_empty_inputs_return_independent_dictionaries(self) -> None:
        for left, right in [({}, {}), ({"a": -1, "b": 0}, {}), ({}, {"b": 0, "a": -1})]:
            with self.subTest(left=left, right=right):
                result = merge(left, right)
                self.assertEqual(list(result.items()), list((left or right).items()))
                self.assertIsNot(result, left)
                self.assertIsNot(result, right)

    def test_same_dictionary_as_both_inputs(self) -> None:
        counts = {"b": -2, "a": 0, "c": 3}
        self.assertEqual(list(merge(counts, counts).items()), [("b", -4), ("a", 0), ("c", 6)])
        self.assertEqual(list(counts.items()), [("b", -2), ("a", 0), ("c", 3)])


if __name__ == "__main__":
    unittest.main()
