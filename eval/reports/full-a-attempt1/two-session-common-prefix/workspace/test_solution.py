"""Regression coverage for the public common API."""

import unittest
from copy import deepcopy
from unittest.mock import call, patch

from solution import common, common_many


class CommonTests(unittest.TestCase):
    def test_empty_input(self) -> None:
        self.assertEqual(common([]), "")

    def test_single_item(self) -> None:
        for item in ("", "flower", "한글🙂"):
            with self.subTest(item=item):
                self.assertEqual(common([item]), item)

    def test_longest_shared_prefix(self) -> None:
        self.assertEqual(common(["flower", "flow", "flight"]), "fl")
        self.assertEqual(common(["prefix", "pre", "prepare"]), "pre")
        self.assertEqual(common(["same", "same"]), "same")

    def test_no_shared_prefix_and_empty_items(self) -> None:
        for items in (["dog", "cat"], ["", "abc"], ["abc", ""]):
            with self.subTest(items=items):
                self.assertEqual(common(items), "")

    def test_matching_is_case_sensitive(self) -> None:
        self.assertEqual(common(["Flower", "flower"]), "")
        self.assertEqual(common(["abC", "abc"]), "ab")

    def test_unicode_characters(self) -> None:
        self.assertEqual(common(["한글🙂가", "한글🙂나"]), "한글🙂")

    def test_input_is_not_mutated(self) -> None:
        items = ["flower", "flow", "flight"]
        original = items.copy()
        self.assertEqual(common(items), "fl")
        self.assertEqual(items, original)


class CommonManyTests(unittest.TestCase):
    def test_empty_batch(self) -> None:
        with patch("solution.common") as single:
            self.assertEqual(common_many([]), [])
        single.assert_not_called()

    def test_batch_results_follow_case_order(self) -> None:
        cases = [(["flower", "flow", "flight"],), ([],),
                 (["한글🙂가", "한글🙂나"],), (["solo"],)]
        self.assertEqual(common_many(cases), ["fl", "", "한글🙂", "solo"])

    def test_batch_does_not_mutate_cases_or_arguments(self) -> None:
        items = ["flower", "flow", "flight"]
        cases = [(items,), (items,), (["same", "same"],)]
        original = deepcopy(cases)
        self.assertEqual(common_many(cases), ["fl", "fl", "same"])
        self.assertEqual(cases, original)
        self.assertIs(cases[0][0], items)
        self.assertIs(cases[1][0], items)

    def test_positional_arguments_are_forwarded(self) -> None:
        cases = [(), ("first", "second"), ("third",)]
        with patch("solution.common", side_effect=[1, 2, 3]) as single:
            self.assertEqual(common_many(cases), [1, 2, 3])
        self.assertEqual(single.call_args_list,
                         [call(), call("first", "second"), call("third")])

    def test_first_exception_is_propagated_unchanged(self) -> None:
        error = ValueError("first failure")
        cases = [(["ok"],), (["fail"],), (["unreached"],)]
        original = deepcopy(cases)
        with patch("solution.common", side_effect=["ok", error, "unreached"]) as single:
            with self.assertRaises(ValueError) as raised:
                common_many(cases)
        self.assertIs(raised.exception, error)
        self.assertEqual(single.call_args_list, [call(["ok"]), call(["fail"])])
        self.assertEqual(cases, original)

    def test_invalid_call_arguments_raise_type_error(self) -> None:
        for case in ((), ([], [])):
            with self.subTest(case=case):
                with self.assertRaises(TypeError):
                    common_many([case])


if __name__ == "__main__":
    unittest.main()
