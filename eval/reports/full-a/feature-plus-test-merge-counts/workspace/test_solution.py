import unittest

from solution import merge


class MergeTests(unittest.TestCase):
    def test_shared_and_distinct_keys(self) -> None:
        left = {"apples": 3, "pears": 2}
        right = {"apples": 4, "oranges": 5}
        self.assertEqual(
            merge(left, right), {"apples": 7, "pears": 2, "oranges": 5}
        )
        self.assertEqual(left, {"apples": 3, "pears": 2})
        self.assertEqual(right, {"apples": 4, "oranges": 5})

    def test_zero_negative_and_large_totals(self) -> None:
        left = {"cancel": 4, "negative": -5, "zero": 0, "large": 10**100}
        right = {"cancel": -4, "negative": 2, "right_zero": 0, "large": 1}
        left_before = left.copy()
        right_before = right.copy()
        self.assertEqual(
            merge(left, right),
            {
                "cancel": 0,
                "negative": -3,
                "zero": 0,
                "right_zero": 0,
                "large": 10**100 + 1,
            },
        )
        self.assertEqual(left, left_before)
        self.assertEqual(right, right_before)

    def test_empty_inputs_return_independent_dictionary(self) -> None:
        for left, right in [({}, {}), ({"a": -2}, {}), ({}, {"b": 0})]:
            with self.subTest(left=left, right=right):
                left_before = left.copy()
                right_before = right.copy()
                result = merge(left, right)
                self.assertEqual(result, {**left, **right})
                self.assertIsNot(result, left)
                self.assertIsNot(result, right)
                result["new"] = 1
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
