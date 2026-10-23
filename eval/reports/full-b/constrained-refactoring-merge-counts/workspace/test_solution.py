import unittest

from solution import merge, merge_legacy


class MergeTests(unittest.TestCase):
    def test_union_and_shared_counts(self) -> None:
        for merge_function in (merge, merge_legacy):
            with self.subTest(api=merge_function.__name__):
                result = merge_function(
                    {"left": 2, "shared": 3},
                    {"right": 4, "shared": 5},
                )
                self.assertIs(type(result), dict)
                self.assertEqual(result, {"left": 2, "shared": 8, "right": 4})

    def test_zero_and_negative_totals_are_preserved(self) -> None:
        for merge_function in (merge, merge_legacy):
            with self.subTest(api=merge_function.__name__):
                self.assertEqual(
                    merge_function(
                        {"cancel": 3, "negative": 2, "left_zero": 0},
                        {"cancel": -3, "negative": -5, "right_zero": 0},
                    ),
                    {"cancel": 0, "negative": -3, "left_zero": 0, "right_zero": 0},
                )

    def test_empty_inputs(self) -> None:
        cases = (
            ({}, {}, {}),
            ({"left": -2}, {}, {"left": -2}),
            ({}, {"right": 0}, {"right": 0}),
        )
        for merge_function in (merge, merge_legacy):
            for left, right, expected in cases:
                with self.subTest(api=merge_function.__name__, left=left, right=right):
                    self.assertEqual(merge_function(left, right), expected)

    def test_inputs_are_unchanged_and_result_is_independent(self) -> None:
        for merge_function in (merge, merge_legacy):
            with self.subTest(api=merge_function.__name__):
                left = {"left": 2, "shared": 3}
                right = {"right": -4, "shared": 5}
                result = merge_function(left, right)
                self.assertEqual(left, {"left": 2, "shared": 3})
                self.assertEqual(right, {"right": -4, "shared": 5})
                self.assertIsNot(result, left)
                self.assertIsNot(result, right)
                result.clear()
                self.assertEqual(left, {"left": 2, "shared": 3})
                self.assertEqual(right, {"right": -4, "shared": 5})

    def test_same_dictionary_can_be_both_inputs(self) -> None:
        for merge_function in (merge, merge_legacy):
            with self.subTest(api=merge_function.__name__):
                counts = {"positive": 2, "zero": 0, "negative": -3}
                self.assertEqual(
                    merge_function(counts, counts),
                    {"positive": 4, "zero": 0, "negative": -6},
                )
                self.assertEqual(counts, {"positive": 2, "zero": 0, "negative": -3})

    def test_existing_errors_propagate_without_mutating_inputs(self) -> None:
        for merge_function in (merge, merge_legacy):
            with self.subTest(api=merge_function.__name__):
                left = {"shared": 1}
                right = {"first": 2, "shared": "invalid"}
                with self.assertRaises(TypeError):
                    merge_function(left, right)
                self.assertEqual(left, {"shared": 1})
                self.assertEqual(right, {"first": 2, "shared": "invalid"})
                with self.assertRaises(TypeError):
                    merge_function(None, {})
                with self.assertRaises(AttributeError):
                    merge_function({}, None)


if __name__ == "__main__":
    unittest.main()
