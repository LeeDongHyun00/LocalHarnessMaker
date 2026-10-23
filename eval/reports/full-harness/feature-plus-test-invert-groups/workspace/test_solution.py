import unittest

from solution import invert


class InvertTests(unittest.TestCase):
    def test_groups_keys_in_insertion_order(self):
        items = {"z": "red", "b": "blue", "a": "red", "c": "blue"}
        original_items = list(items.items())

        self.assertEqual(invert(items), {"red": ["z", "a"], "blue": ["b", "c"]})
        self.assertEqual(list(items.items()), original_items)

    def test_empty_input(self):
        items: dict[str, str] = {}

        self.assertEqual(invert(items), {})
        self.assertEqual(items, {})

    def test_single_entry_with_empty_key_and_value(self):
        items = {"": ""}

        self.assertEqual(invert(items), {"": [""]})
        self.assertEqual(items, {"": ""})

    def test_all_keys_share_one_value(self):
        items = {"third": "", "first": "", "second": ""}

        result = invert(items)

        self.assertEqual(result, {"": ["third", "first", "second"]})
        result[""].append("new")
        self.assertEqual(list(items.items()), [("third", ""), ("first", ""), ("second", "")])


if __name__ == "__main__":
    unittest.main()
