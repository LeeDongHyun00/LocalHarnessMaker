import unittest

from solution import merge, merge_legacy


class MergeTests(unittest.TestCase):
    def test_union_preserves_zero_and_negative_totals(self) -> None:
        for function in (merge, merge_legacy):
            with self.subTest(function=function.__name__):
                left = {"shared": 4, "cancel": 2, "left": -3}
                right = {"shared": -7, "cancel": -2, "right": 0}
                result = function(left=left, right=right)
                self.assertIs(type(result), dict)
                self.assertEqual(
                    result, {"shared": -3, "cancel": 0, "left": -3, "right": 0}
                )
                self.assertEqual(left, {"shared": 4, "cancel": 2, "left": -3})
                self.assertEqual(right, {"shared": -7, "cancel": -2, "right": 0})

    def test_empty_inputs_return_independent_dictionaries(self) -> None:
        for function in (merge, merge_legacy):
            for left, right in (({}, {}), ({"a": 1}, {}), ({}, {"a": 1})):
                with self.subTest(function=function.__name__, left=left, right=right):
                    result = function(left, right)
                    self.assertEqual(result, {**left, **right})
                    self.assertIsNot(result, left)
                    self.assertIsNot(result, right)
                    result["new"] = 2
                    self.assertNotIn("new", left)
                    self.assertNotIn("new", right)

    def test_same_input_can_be_passed_twice(self) -> None:
        for function in (merge, merge_legacy):
            with self.subTest(function=function.__name__):
                counts = {"positive": 3, "negative": -2, "zero": 0}
                self.assertEqual(
                    function(counts, counts),
                    {"positive": 6, "negative": -4, "zero": 0},
                )
                self.assertEqual(counts, {"positive": 3, "negative": -2, "zero": 0})

    def test_errors_preserve_inputs(self) -> None:
        for function in (merge, merge_legacy):
            with self.subTest(function=function.__name__):
                left = {"a": 1}
                right = {"a": 2, "bad": "invalid"}
                with self.assertRaises(TypeError):
                    function(left, right)
                self.assertEqual(left, {"a": 1})
                self.assertEqual(right, {"a": 2, "bad": "invalid"})
                with self.assertRaises(TypeError):
                    function(None, {})
                with self.assertRaises(AttributeError):
                    function({}, None)


if __name__ == "__main__":
    unittest.main()
