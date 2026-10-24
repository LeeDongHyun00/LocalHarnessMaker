"""Regression coverage for the public invert API."""

import unittest
from unittest.mock import call, patch

from solution import invert, invert_many


class InvertTests(unittest.TestCase):
    def test_groups_keys_by_value(self) -> None:
        self.assertEqual(
            invert({"apple": "fruit", "carrot": "vegetable", "pear": "fruit"}),
            {"fruit": ["apple", "pear"], "vegetable": ["carrot"]},
        )

    def test_preserves_insertion_order_within_groups(self) -> None:
        items = {"z": "shared", "middle": "other", "a": "shared", "m": "shared"}
        self.assertEqual(invert(items)["shared"], ["z", "a", "m"])

    def test_empty_input(self) -> None:
        self.assertEqual(invert({}), {})

    def test_does_not_mutate_input_and_returns_independent_lists(self) -> None:
        items = {"first": "same", "second": "same"}
        original_items = list(items.items())
        result = invert(items)
        result["same"].append("extra")
        self.assertEqual(list(items.items()), original_items)
        self.assertEqual(invert(items), {"same": ["first", "second"]})


class InvertManyTests(unittest.TestCase):
    def test_returns_results_in_case_order(self) -> None:
        self.assertEqual(
            invert_many([({"a": "x", "b": "x"},), ({},), ({"c": "y"},)]),
            [{"x": ["a", "b"]}, {}, {"y": ["c"]}],
        )

    def test_empty_cases(self) -> None:
        self.assertEqual(invert_many([]), [])

    def test_preserves_cases_and_arguments_and_returns_independent_results(self) -> None:
        items = {"z": "shared", "a": "shared", "middle": "other"}
        cases = [(items,), (items,)]
        original_cases = cases.copy()
        original_items = list(items.items())

        results = invert_many(cases)
        self.assertEqual(cases, original_cases)
        for case, original_case in zip(cases, original_cases):
            self.assertIs(case, original_case)
            self.assertIs(case[0], items)
        self.assertEqual(results[0]["shared"], ["z", "a"])
        results[0]["shared"].append("extra")
        self.assertEqual(results[1]["shared"], ["z", "a"])
        self.assertEqual(list(items.items()), original_items)

    def test_forwards_positional_arguments_and_propagates_first_exception(self) -> None:
        failure = ValueError("first failure")
        cases = [({"a": "x"},), ({"b": "y"},), ({"c": "z"},)]
        with patch("solution.invert", side_effect=[{"x": ["a"]}, failure]) as mocked:
            with self.assertRaises(ValueError) as raised:
                invert_many(cases)
        self.assertIs(raised.exception, failure)
        self.assertEqual(mocked.call_args_list, [call(*cases[0]), call(*cases[1])])


if __name__ == "__main__":
    unittest.main()
