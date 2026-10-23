"""Public regression tests for common."""

import unittest
from copy import deepcopy
from unittest.mock import call, patch

from solution import common, common_many


class CommonTests(unittest.TestCase):
    def test_empty_input(self) -> None:
        self.assertEqual(common([]), "")

    def test_single_item(self) -> None:
        for item in ("flower", "", "한글🙂"):
            with self.subTest(item=item):
                self.assertEqual(common([item]), item)

    def test_shared_prefix(self) -> None:
        self.assertEqual(common(["flower", "flow", "flight"]), "fl")

    def test_case_sensitive(self) -> None:
        self.assertEqual(common(["Flower", "flower"]), "")
        self.assertEqual(common(["abC", "abc"]), "ab")

    def test_no_common_prefix_and_empty_item(self) -> None:
        for items in (["dog", "cat"], ["", "abc"], ["abc", ""]):
            with self.subTest(items=items):
                self.assertEqual(common(items), "")

    def test_whole_item_and_identical_items(self) -> None:
        self.assertEqual(common(["prefix", "pre", "present"]), "pre")
        self.assertEqual(common(["same", "same"]), "same")

    def test_unicode_characters(self) -> None:
        self.assertEqual(common(["한글🙂a", "한글🙂b"]), "한글🙂")

    def test_input_is_not_mutated(self) -> None:
        items = ["flower", "flow", "flight"]
        original = items.copy()
        self.assertEqual(common(items), "fl")
        self.assertEqual(items, original)


class CommonManyTests(unittest.TestCase):
    def test_many_results_in_order_without_mutation(self) -> None:
        cases = [(["flower", "flow", "flight"],), ([],),
                 (["한글🙂a", "한글🙂b"],), (["same"],)]
        original = deepcopy(cases)
        self.assertEqual(common_many(cases), ["fl", "", "한글🙂", "same"])
        self.assertEqual(cases, original)

    def test_many_empty(self) -> None:
        with patch("solution.common") as mocked:
            self.assertEqual(common_many([]), [])
        mocked.assert_not_called()

    def test_many_forwards_positional_arguments(self) -> None:
        items = ["abc"]
        with patch("solution.common", return_value="result") as mocked:
            self.assertEqual(common_many([(items, "extra")]), ["result"])
        mocked.assert_called_once_with(items, "extra")
        self.assertIs(mocked.call_args.args[0], items)

    def test_many_propagates_first_exception_and_stops(self) -> None:
        error = ValueError("first failure")
        cases = [(["first"],), (["second"],), (["third"],)]
        original = deepcopy(cases)
        with patch("solution.common", side_effect=["first", error, "third"]) as mocked:
            with self.assertRaises(ValueError) as raised:
                common_many(cases)
        self.assertIs(raised.exception, error)
        self.assertEqual(mocked.call_args_list, [call(*case) for case in cases[:2]])
        self.assertEqual(cases, original)


if __name__ == "__main__":
    unittest.main()
