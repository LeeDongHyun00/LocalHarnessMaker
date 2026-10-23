import unittest

from solution import merge


class MergeTests(unittest.TestCase):
    def test_union_adds_shared_counts(self) -> None:
        self.assertEqual(
            merge({"left": 2, "shared": 3}, {"shared": 4, "right": 5}),
            {"left": 2, "shared": 7, "right": 5},
        )

    def test_zero_and_negative_counts_are_retained(self) -> None:
        self.assertEqual(
            merge(
                {"zero": 3, "negative": -5, "left_zero": 0},
                {"zero": -3, "negative": 2, "right_zero": 0, "right_negative": -4},
            ),
            {"zero": 0, "negative": -3, "left_zero": 0,
             "right_zero": 0, "right_negative": -4},
        )

    def test_input_values_and_order_are_preserved(self) -> None:
        left = {"second": 2, "shared": 3, "first": 1}
        right = {"last": 4, "shared": 5, "next": 6}
        left_before = list(left.items())
        right_before = list(right.items())

        result = merge(left, right)

        self.assertEqual(
            list(result.items()),
            [("second", 2), ("shared", 8), ("first", 1), ("last", 4), ("next", 6)],
        )
        self.assertEqual(list(left.items()), left_before)
        self.assertEqual(list(right.items()), right_before)
        self.assertIsNot(result, left)
        self.assertIsNot(result, right)

    def test_empty_inputs_return_independent_dictionaries(self) -> None:
        for left, right in [({}, {}), ({"a": -2}, {}), ({}, {"b": 0})]:
            with self.subTest(left=left, right=right):
                result = merge(left, right)
                self.assertEqual(result, left | right)
                self.assertIsNot(result, left)
                self.assertIsNot(result, right)

    def test_same_dictionary_can_be_used_for_both_inputs(self) -> None:
        counts = {"positive": 3, "zero": 0, "negative": -2}
        before = list(counts.items())

        result = merge(counts, counts)

        self.assertEqual(
            list(result.items()), [("positive", 6), ("zero", 0), ("negative", -4)]
        )
        self.assertEqual(list(counts.items()), before)
        self.assertIsNot(result, counts)


if __name__ == "__main__":
    unittest.main()
