"""Regression tests for the public invert API."""

import unittest

from solution import invert


class InvertTests(unittest.TestCase):
    def test_empty_input(self) -> None:
        self.assertEqual(invert({}), {})

    def test_repeated_values_keep_all_keys_in_insertion_order(self) -> None:
        items = {"z": "blue", "b": "red", "a": "blue", "y": "red"}

        result = invert(items)

        self.assertEqual(result, {"blue": ["z", "a"], "red": ["b", "y"]})
        self.assertEqual(list(result), ["blue", "red"])

    def test_preserves_exact_values_and_input_order(self) -> None:
        items = {"second": " Mixed Case ", "first": "", "third": "mixed case"}
        original = list(items.items())

        result = invert(items)

        self.assertEqual(
            list(result.items()),
            [(" Mixed Case ", ["second"]), ("", ["first"]),
             ("mixed case", ["third"])],
        )
        self.assertEqual(list(items.items()), original)

    def test_result_lists_are_independent(self) -> None:
        items = {"a": "same", "b": "same", "c": "other"}
        original = list(items.items())
        first = invert(items)
        second = invert(items)

        first["same"].append("extra")

        self.assertEqual(first["other"], ["c"])
        self.assertEqual(second, {"same": ["a", "b"], "other": ["c"]})
        self.assertEqual(list(items.items()), original)


if __name__ == "__main__":
    unittest.main()
