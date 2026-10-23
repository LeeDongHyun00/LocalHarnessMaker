"""Tests for the public invert API."""

import unittest

from solution import invert


class InvertTests(unittest.TestCase):
    def test_groups_keys_in_insertion_order_without_mutating_input(self) -> None:
        items = {
            "zebra": "animal",
            "pear": "fruit",
            "ant": "animal",
            "apple": "fruit",
            "oak": "tree",
        }
        original_items = list(items.items())

        self.assertEqual(
            invert(items),
            {
                "animal": ["zebra", "ant"],
                "fruit": ["pear", "apple"],
                "tree": ["oak"],
            },
        )
        self.assertEqual(list(items.items()), original_items)

    def test_all_keys_share_one_value(self) -> None:
        self.assertEqual(
            invert({"third": "same", "first": "same", "second": "same"}),
            {"same": ["third", "first", "second"]},
        )

    def test_single_entry(self) -> None:
        self.assertEqual(invert({"key": "value"}), {"value": ["key"]})

    def test_empty_string_keys_and_values(self) -> None:
        self.assertEqual(
            invert({"": "", "another": "", "last": "value"}),
            {"": ["", "another"], "value": ["last"]},
        )

    def test_empty_input(self) -> None:
        self.assertEqual(invert({}), {})


if __name__ == "__main__":
    unittest.main()
