"""Regression coverage for the public invert API."""

import unittest
from unittest.mock import call, patch

from solution import invert, invert_many


class InvertTests(unittest.TestCase):
    def test_empty_input(self) -> None:
        self.assertEqual(invert({}), {})

    def test_distinct_values(self) -> None:
        self.assertEqual(
            invert({"first": "red", "second": "blue"}),
            {"red": ["first"], "blue": ["second"]},
        )

    def test_repeated_values_preserve_key_insertion_order(self) -> None:
        self.assertEqual(
            invert({"z": "red", "b": "blue", "a": "red", "y": "blue"}),
            {"red": ["z", "a"], "blue": ["b", "y"]},
        )

    def test_empty_strings_are_valid_keys_and_values(self) -> None:
        self.assertEqual(
            invert({"": "", "other": "", "last": "value"}),
            {"": ["", "other"], "value": ["last"]},
        )

    def test_input_is_unchanged_and_results_are_independent(self) -> None:
        items = {"first": "shared", "second": "shared"}
        original_entries = list(items.items())

        result = invert(items)
        self.assertEqual(list(items.items()), original_entries)
        result["shared"].append("extra")

        self.assertEqual(list(items.items()), original_entries)
        self.assertEqual(invert(items), {"shared": ["first", "second"]})


class InvertManyTests(unittest.TestCase):
    def test_empty_batch(self) -> None:
        with patch("solution.invert") as mocked_invert:
            self.assertEqual(invert_many([]), [])
        mocked_invert.assert_not_called()

    def test_results_follow_case_order(self) -> None:
        self.assertEqual(
            invert_many([
                ({"z": "red", "a": "red", "b": "blue"},),
                ({},),
                ({"last": "green"},),
            ]),
            [{"red": ["z", "a"], "blue": ["b"]}, {}, {"green": ["last"]}],
        )

    def test_cases_and_arguments_are_unchanged(self) -> None:
        items = {"first": "shared", "second": "shared"}
        cases = [(items,), (items,)]
        original_cases = cases.copy()
        original_entries = list(items.items())

        results = invert_many(cases)

        self.assertEqual(cases, original_cases)
        for case, original_case in zip(cases, original_cases):
            self.assertIs(case, original_case)
            self.assertIs(case[0], items)
        self.assertEqual(list(items.items()), original_entries)
        results[0]["shared"].append("extra")
        self.assertEqual(results[1], {"shared": ["first", "second"]})
        self.assertEqual(list(items.items()), original_entries)

    def test_first_exception_propagates_unchanged_and_stops_batch(self) -> None:
        error = ValueError("sentinel failure")
        cases = [({"first": "red"},), ({"second": "blue"},), ({},)]
        with patch("solution.invert", side_effect=[{}, error, RuntimeError()]) as mocked_invert:
            with self.assertRaises(ValueError) as raised:
                invert_many(cases)

        self.assertIs(raised.exception, error)
        self.assertEqual(mocked_invert.call_args_list, [call(*cases[0]), call(*cases[1])])

    def test_invalid_positional_argument_counts_raise(self) -> None:
        for case in [(), ({}, {})]:
            with self.subTest(case=case):
                with self.assertRaises(TypeError):
                    invert_many([case])


if __name__ == "__main__":
    unittest.main()
