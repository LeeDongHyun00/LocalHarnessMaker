"""Regression tests for the public invert API."""

import unittest

from solution import invert


class InvertTests(unittest.TestCase):
    def test_groups_repeated_values_in_insertion_order(self) -> None:
        items = {
            "zebra": "blue",
            "yellow": "red",
            "apple": "blue",
            "banana": "red",
            "middle": "blue",
        }

        result = invert(items)

        self.assertEqual(
            result,
            {"blue": ["zebra", "apple", "middle"], "red": ["yellow", "banana"]},
        )
        self.assertEqual(list(result), ["blue", "red"])

    def test_empty_input_returns_empty_dictionary(self) -> None:
        self.assertEqual(invert({}), {})

    def test_preserves_input_values_and_order(self) -> None:
        items = {"third": "shared", "first": "unique", "second": "shared"}
        original_items = list(items.items())

        result = invert(items)

        self.assertEqual(list(items.items()), original_items)
        result["shared"].append("extra")
        self.assertEqual(list(items.items()), original_items)
        self.assertEqual(invert(items)["shared"], ["third", "second"])

    def test_preserves_empty_whitespace_and_case_sensitive_values(self) -> None:
        items = {"": "", "one": " Value ", "two": "value", "three": "Value"}

        self.assertEqual(
            invert(items),
            {"": [""], " Value ": ["one"], "value": ["two"], "Value": ["three"]},
        )


if __name__ == "__main__":
    unittest.main()
