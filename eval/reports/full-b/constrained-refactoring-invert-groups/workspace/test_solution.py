import unittest

from solution import invert, invert_legacy


class InvertTests(unittest.TestCase):
    def test_groups_keys_in_insertion_order(self) -> None:
        items = {"z": "shared", "b": "other", "a": "shared", "c": "other"}
        expected = {"shared": ["z", "a"], "other": ["b", "c"]}

        for function in (invert, invert_legacy):
            with self.subTest(function=function.__name__):
                result = function(items)
                self.assertEqual(result, expected)
                self.assertEqual(list(result), list(expected))
                self.assertIs(type(result), dict)
                for keys in result.values():
                    self.assertIs(type(keys), list)

    def test_empty_input(self) -> None:
        for function in (invert, invert_legacy):
            with self.subTest(function=function.__name__):
                result = function({})
                self.assertEqual(result, {})
                self.assertIs(type(result), dict)

    def test_preserves_input_and_returns_independent_collections(self) -> None:
        for function in (invert, invert_legacy):
            with self.subTest(function=function.__name__):
                items = {"z": "shared", "b": "other", "a": "shared"}
                original = list(items.items())

                result = function(items)
                self.assertEqual(list(items.items()), original)
                result["shared"].append("new")
                result["other"].clear()
                result["extra"] = []

                self.assertEqual(list(items.items()), original)
                self.assertEqual(
                    function(items), {"shared": ["z", "a"], "other": ["b"]}
                )

    def test_unhashable_values_raise_without_mutating_input(self) -> None:
        for function in (invert, invert_legacy):
            with self.subTest(function=function.__name__):
                value: list[str] = []
                items = {"valid": "group", "invalid": value}
                original = list(items.items())

                with self.assertRaises(TypeError):
                    function(items)

                self.assertEqual(list(items.items()), original)
                self.assertIs(items["invalid"], value)
                self.assertEqual(value, [])

    def test_inputs_without_items_raise_attribute_error(self) -> None:
        for function in (invert, invert_legacy):
            for items in (None, []):
                with self.subTest(function=function.__name__, items=items):
                    with self.assertRaises(AttributeError):
                        function(items)


if __name__ == "__main__":
    unittest.main()
