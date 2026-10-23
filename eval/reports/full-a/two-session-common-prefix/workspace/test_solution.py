"""Regression coverage for the public common API."""

import unittest
from copy import deepcopy
from unittest.mock import call, patch

from solution import common, common_many


class CommonTests(unittest.TestCase):
    def test_empty_input(self) -> None:
        self.assertEqual(common([]), "")

    def test_one_item(self) -> None:
        for item in ("", "solo", "Mixed Case", "한글🙂"):
            with self.subTest(item=item):
                self.assertEqual(common([item]), item)

    def test_shared_prefix(self) -> None:
        self.assertEqual(common(["flower", "flow", "flight"]), "fl")

    def test_shortest_item_and_identical_items(self) -> None:
        self.assertEqual(common(["prefixes", "prefix", "prefixing"]), "prefix")
        self.assertEqual(common(["same", "same"]), "same")

    def test_no_common_prefix_and_case_sensitivity(self) -> None:
        self.assertEqual(common(["dog", "racecar", "car"]), "")
        self.assertEqual(common(["Apple", "apple"]), "")
        self.assertEqual(common(["aB", "ab"]), "a")

    def test_empty_item(self) -> None:
        for items in (["", "abc"], ["abc", ""], ["abc", "abd", ""]):
            with self.subTest(items=items):
                self.assertEqual(common(items), "")

    def test_unicode_characters(self) -> None:
        self.assertEqual(common(["한글🙂가", "한글🙂나"]), "한글🙂")

    def test_input_is_not_mutated(self) -> None:
        items = ["flower", "flow", "flight"]
        original = items.copy()
        self.assertEqual(common(items), "fl")
        self.assertEqual(items, original)


class CommonManyTests(unittest.TestCase):
    def test_empty_cases(self) -> None:
        self.assertEqual(common_many([]), [])

    def test_results_in_case_order_and_inputs_preserved(self) -> None:
        shared = ["flower", "flow", "flight"]
        cases = [(shared,), ([],), (["한글🙂가", "한글🙂나"],), (shared,)]
        original = deepcopy(cases)
        self.assertEqual(common_many(cases), ["fl", "", "한글🙂", "fl"])
        self.assertEqual(cases, original)
        self.assertIs(cases[0][0], shared)
        self.assertIs(cases[3][0], shared)

    def test_first_exception_propagates_unchanged_and_stops_calls(self) -> None:
        failure = ValueError("first failure")
        cases = [(["first"],), (["second"],), (["third"],)]
        original = deepcopy(cases)
        with patch("solution.common", side_effect=["first", failure, RuntimeError()]) as mocked:
            with self.assertRaises(ValueError) as raised:
                common_many(cases)
        self.assertIs(raised.exception, failure)
        self.assertEqual(mocked.call_args_list, [call(*cases[0]), call(*cases[1])])
        self.assertEqual(cases, original)

    def test_invalid_positional_arguments_raise_type_error(self) -> None:
        for case in ((), ([], [])):
            with self.subTest(case=case):
                with self.assertRaises(TypeError):
                    common_many([case])


if __name__ == "__main__":
    unittest.main()
