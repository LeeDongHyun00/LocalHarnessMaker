"""Regression coverage for the public common API."""

import unittest
from copy import deepcopy
from unittest.mock import call, patch

from solution import common, common_many


class CommonTests(unittest.TestCase):
    def test_empty_input(self) -> None:
        self.assertEqual(common([]), "")

    def test_single_item(self) -> None:
        for item in ("flower", "", "한글🌸"):
            with self.subTest(item=item):
                self.assertEqual(common([item]), item)

    def test_longest_shared_prefix(self) -> None:
        self.assertEqual(common(["flower", "flow", "flight"]), "fl")
        self.assertEqual(common(["prefix", "pre", "present"]), "pre")
        self.assertEqual(common(["same", "same"]), "same")

    def test_case_sensitive_matching(self) -> None:
        self.assertEqual(common(["Flower", "flower"]), "")
        self.assertEqual(common(["abC", "abc"]), "ab")

    def test_empty_item_and_no_shared_prefix(self) -> None:
        self.assertEqual(common(["abc", "", "abd"]), "")
        self.assertEqual(common(["", "abc"]), "")
        self.assertEqual(common(["dog", "racecar", "car"]), "")

    def test_unicode_characters(self) -> None:
        self.assertEqual(common(["한글🌸a", "한글🌸b"]), "한글🌸")

    def test_input_is_not_mutated(self) -> None:
        items = ["flower", "flow", "flight"]
        original = items.copy()
        self.assertEqual(common(items), "fl")
        self.assertEqual(items, original)


class CommonManyTests(unittest.TestCase):
    def test_batch_order_and_input_preservation(self) -> None:
        cases = [(["flower", "flow", "flight"],), ([],), (["한글a", "한글b"],)]
        original = deepcopy(cases)
        arguments = [case[0] for case in cases]
        self.assertEqual(common_many(cases), ["fl", "", "한글"])
        self.assertEqual(cases, original)
        for case, argument in zip(cases, arguments):
            self.assertIs(case[0], argument)

    def test_empty_batch(self) -> None:
        with patch("solution.common") as mocked_common:
            self.assertEqual(common_many([]), [])
            mocked_common.assert_not_called()

    def test_positional_argument_forwarding(self) -> None:
        cases = [(), ("first",), ("second", "third")]
        with patch("solution.common", side_effect=[1, 2, 3]) as mocked_common:
            self.assertEqual(common_many(cases), [1, 2, 3])
            self.assertEqual(
                mocked_common.call_args_list,
                [call(), call("first"), call("second", "third")],
            )

    def test_first_exception_propagates_unchanged_and_stops_batch(self) -> None:
        error = ValueError("first failure")
        cases = [(["ok"],), (["fail"],), (["unreached"],)]
        original = deepcopy(cases)
        with patch("solution.common", side_effect=["ok", error, "unreached"]) as mocked_common:
            with self.assertRaises(ValueError) as caught:
                common_many(cases)
            self.assertIs(caught.exception, error)
            self.assertEqual(mocked_common.call_args_list, [call(["ok"]), call(["fail"])])
        self.assertEqual(cases, original)


if __name__ == "__main__":
    unittest.main()
