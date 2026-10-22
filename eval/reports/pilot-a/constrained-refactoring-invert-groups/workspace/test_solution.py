import unittest

from solution import invert, invert_legacy


class InvertTests(unittest.TestCase):
    def test_groups_keys_in_insertion_order_without_mutating_input(self):
        for function in (invert, invert_legacy):
            with self.subTest(function=function.__name__):
                items = {"third": "b", "second": "a", "first": "b"}
                original = list(items.items())
                result = function(items)
                self.assertIsInstance(result, dict)
                self.assertEqual(result, {"b": ["third", "first"], "a": ["second"]})
                self.assertEqual(list(result), ["b", "a"])
                self.assertTrue(all(isinstance(keys, list) for keys in result.values()))
                self.assertEqual(list(items.items()), original)
                result["b"].append("extra")
                self.assertEqual(list(items.items()), original)
                self.assertEqual(function(items)["b"], ["third", "first"])

    def test_empty_input(self):
        for function in (invert, invert_legacy):
            with self.subTest(function=function.__name__):
                items = {}
                result = function(items)
                self.assertEqual(result, {})
                self.assertIsNot(result, items)

    def test_unhashable_values_raise_type_error_without_mutation(self):
        for function in (invert, invert_legacy):
            with self.subTest(function=function.__name__):
                value = ["unhashable"]
                items = {"valid": "a", "invalid": value}
                with self.assertRaises(TypeError):
                    function(items)
                self.assertEqual(list(items.items()), [("valid", "a"), ("invalid", value)])
                self.assertEqual(value, ["unhashable"])

    def test_input_without_items_raises_attribute_error(self):
        for function in (invert, invert_legacy):
            with self.subTest(function=function.__name__):
                with self.assertRaises(AttributeError):
                    function(None)


if __name__ == "__main__":
    unittest.main()
