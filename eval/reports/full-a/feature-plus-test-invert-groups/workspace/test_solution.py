import unittest

from solution import invert


class InvertTests(unittest.TestCase):
    def test_groups_keys_in_insertion_order_without_mutating_input(self) -> None:
        items = {"z": "red", "b": "blue", "a": "red", "c": "blue"}
        original = items.copy()

        result = invert(items)

        self.assertEqual(result, {"red": ["z", "a"], "blue": ["b", "c"]})
        self.assertEqual(list(items.items()), list(original.items()))

    def test_single_item(self) -> None:
        self.assertEqual(invert({"key": "value"}), {"value": ["key"]})

    def test_empty_strings_are_valid_keys_and_values(self) -> None:
        self.assertEqual(invert({"": "", "key": ""}), {"": ["", "key"]})

    def test_empty_input(self) -> None:
        self.assertEqual(invert({}), {})


if __name__ == "__main__":
    unittest.main()
