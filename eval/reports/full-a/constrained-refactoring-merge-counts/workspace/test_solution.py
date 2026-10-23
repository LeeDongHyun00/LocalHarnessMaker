import unittest

from solution import merge, merge_legacy


class MergeTests(unittest.TestCase):
    def test_union_and_shared_counts_preserve_zero_and_negative_totals(self):
        for function in (merge, merge_legacy):
            with self.subTest(function=function.__name__):
                self.assertEqual(
                    function(
                        {"left": 2, "zero": 3, "negative": -4},
                        {"right": 5, "zero": -3, "negative": 1},
                    ),
                    {"left": 2, "right": 5, "zero": 0, "negative": -3},
                )

    def test_inputs_are_unchanged_and_result_is_independent(self):
        for function in (merge, merge_legacy):
            with self.subTest(function=function.__name__):
                left = {"shared": 2, "left": 0}
                right = {"shared": -2, "right": -1}
                result = function(left, right)
                self.assertEqual(left, {"shared": 2, "left": 0})
                self.assertEqual(right, {"shared": -2, "right": -1})
                self.assertIs(type(result), dict)
                self.assertIsNot(result, left)
                self.assertIsNot(result, right)
                result["shared"] = 99
                self.assertEqual(left["shared"], 2)
                self.assertEqual(right["shared"], -2)

    def test_empty_and_aliased_inputs(self):
        for function in (merge, merge_legacy):
            with self.subTest(function=function.__name__):
                self.assertEqual(function({}, {}), {})
                counts = {"positive": 2, "zero": 0, "negative": -1}
                self.assertEqual(function(counts, {}), counts)
                self.assertEqual(function({}, counts), counts)
                self.assertEqual(
                    function(counts, counts),
                    {"positive": 4, "zero": 0, "negative": -2},
                )
                self.assertEqual(counts, {"positive": 2, "zero": 0, "negative": -1})

    def test_invalid_addition_preserves_error_and_inputs(self):
        for function in (merge, merge_legacy):
            with self.subTest(function=function.__name__):
                left = {"valid": 1, "invalid": 2}
                right = {"valid": 3, "invalid": "text"}
                with self.assertRaises(TypeError):
                    function(left, right)
                self.assertEqual(left, {"valid": 1, "invalid": 2})
                self.assertEqual(right, {"valid": 3, "invalid": "text"})


if __name__ == "__main__":
    unittest.main()
