import unittest

from solution import merge


class MergeTests(unittest.TestCase):
    def test_union_and_shared_counts_without_mutation(self) -> None:
        left = {"left": 2, "shared": 3}
        right = {"shared": 4, "right": 5}
        result = merge(left, right)
        self.assertEqual(result, {"left": 2, "shared": 7, "right": 5})
        self.assertEqual(left, {"left": 2, "shared": 3})
        self.assertEqual(right, {"shared": 4, "right": 5})
        self.assertIsNot(result, left)
        self.assertIsNot(result, right)

    def test_zero_and_negative_totals_are_preserved(self) -> None:
        left = {"cancel": 5, "negative": -4, "left_zero": 0}
        right = {"cancel": -5, "negative": 1, "right_zero": 0, "debt": -2}
        left_before = left.copy()
        right_before = right.copy()
        self.assertEqual(
            merge(left, right),
            {"cancel": 0, "negative": -3, "left_zero": 0,
             "right_zero": 0, "debt": -2},
        )
        self.assertEqual(left, left_before)
        self.assertEqual(right, right_before)

    def test_empty_inputs(self) -> None:
        for left, right in [({}, {}), ({"a": -1}, {}), ({}, {"a": 0})]:
            with self.subTest(left=left, right=right):
                left_before = left.copy()
                right_before = right.copy()
                result = merge(left, right)
                self.assertEqual(result, left | right)
                self.assertIsNot(result, left)
                self.assertIsNot(result, right)
                self.assertEqual(left, left_before)
                self.assertEqual(right, right_before)

    def test_same_dictionary_as_both_inputs(self) -> None:
        counts = {"positive": 3, "negative": -2, "zero": 0}
        self.assertEqual(
            merge(counts, counts), {"positive": 6, "negative": -4, "zero": 0}
        )
        self.assertEqual(counts, {"positive": 3, "negative": -2, "zero": 0})


if __name__ == "__main__":
    unittest.main()
