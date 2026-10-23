import unittest

from solution import merge


class MergeTests(unittest.TestCase):
    def test_shared_counts_are_added_and_all_keys_are_retained(self) -> None:
        left = {"apples": 3, "pears": 2}
        right = {"pears": 4, "oranges": 5}

        self.assertEqual(
            merge(left, right), {"apples": 3, "pears": 6, "oranges": 5}
        )

    def test_zero_and_negative_totals_are_preserved(self) -> None:
        left = {
            "cancelled": 5,
            "debt": -4,
            "shared_zero": 0,
            "left_zero": 0,
            "left_negative": -7,
        }
        right = {
            "cancelled": -5,
            "debt": 1,
            "shared_zero": 0,
            "right_zero": 0,
            "right_negative": -2,
        }

        self.assertEqual(
            merge(left, right),
            {
                "cancelled": 0,
                "debt": -3,
                "shared_zero": 0,
                "left_zero": 0,
                "left_negative": -7,
                "right_zero": 0,
                "right_negative": -2,
            },
        )

    def test_key_order_preserves_left_then_new_right_keys(self) -> None:
        left = {"zebra": 1, "ant": 2, "fox": 3}
        right = {"fox": 4, "yak": 5, "ant": 6, "bee": 7}

        self.assertEqual(
            list(merge(left, right).items()),
            [("zebra", 1), ("ant", 8), ("fox", 7), ("yak", 5), ("bee", 7)],
        )

    def test_inputs_are_unchanged_and_result_is_independent(self) -> None:
        left = {"shared": 4, "left_only": 0}
        right = {"right_only": -3, "shared": -1}
        left_before = list(left.items())
        right_before = list(right.items())

        result = merge(left, right)

        self.assertEqual(list(left.items()), left_before)
        self.assertEqual(list(right.items()), right_before)
        self.assertIsNot(result, left)
        self.assertIsNot(result, right)

        result["shared"] = 99
        result["new"] = 1
        del result["left_only"]

        self.assertEqual(list(left.items()), left_before)
        self.assertEqual(list(right.items()), right_before)

    def test_empty_inputs_return_a_fresh_dictionary(self) -> None:
        cases = [
            ({}, {}, {}),
            ({}, {"zero": 0, "negative": -2}, {"zero": 0, "negative": -2}),
            ({"b": 2, "a": 0}, {}, {"b": 2, "a": 0}),
        ]
        for left, right, expected in cases:
            with self.subTest(left=left, right=right):
                result = merge(left, right)

                self.assertEqual(result, expected)
                self.assertEqual(list(result), list(expected))
                self.assertIsNot(result, left)
                self.assertIsNot(result, right)

    def test_same_dictionary_can_be_used_for_both_inputs(self) -> None:
        counts = {"positive": 3, "zero": 0, "negative": -2}
        before = list(counts.items())

        result = merge(counts, counts)

        self.assertEqual(result, {"positive": 6, "zero": 0, "negative": -4})
        self.assertEqual(list(result), list(counts))
        self.assertEqual(list(counts.items()), before)
        self.assertIsNot(result, counts)


if __name__ == "__main__":
    unittest.main()
