import unittest

from solution import invert, invert_legacy


class InvertTests(unittest.TestCase):
    def test_grouping_preserves_insertion_order(self) -> None:
        items = {"third": "b", "first": "a", "second": "b", "fourth": "a"}
        expected = {"b": ["third", "second"], "a": ["first", "fourth"]}
        for function in (invert, invert_legacy):
            with self.subTest(function=function.__name__):
                result = function(items)
                self.assertIsInstance(result, dict)
                self.assertEqual(result, expected)
                self.assertEqual(list(result), ["b", "a"])

    def test_empty_input(self) -> None:
        for function in (invert, invert_legacy):
            with self.subTest(function=function.__name__):
                self.assertEqual(function({}), {})

    def test_input_is_unchanged_and_results_are_independent(self) -> None:
        for function in (invert, invert_legacy):
            with self.subTest(function=function.__name__):
                items = {"one": "same", "two": "same"}
                original = list(items.items())
                result = function(items)
                result["same"].append("extra")
                self.assertEqual(list(items.items()), original)
                self.assertEqual(function(items), {"same": ["one", "two"]})

    def test_unhashable_values_raise_without_mutating_input(self) -> None:
        for function in (invert, invert_legacy):
            with self.subTest(function=function.__name__):
                items = {"valid": "value", "invalid": []}
                with self.assertRaises(TypeError):
                    function(items)
                self.assertEqual(items, {"valid": "value", "invalid": []})

    def test_missing_items_method_raises_attribute_error(self) -> None:
        for function in (invert, invert_legacy):
            with self.subTest(function=function.__name__):
                with self.assertRaises(AttributeError):
                    function(None)


if __name__ == "__main__":
    unittest.main()
