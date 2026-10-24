"""Regression tests for the public inclusive API."""

import unittest
from unittest.mock import call, patch

from solution import inclusive, inclusive_many


class InclusiveTests(unittest.TestCase):
    def test_ascending_endpoints_are_included(self) -> None:
        self.assertEqual(inclusive(2, 5), [2, 3, 4, 5])

    def test_descending_endpoints_are_included(self) -> None:
        self.assertEqual(inclusive(5, 2), [5, 4, 3, 2])

    def test_equal_endpoints_give_singleton(self) -> None:
        for endpoint in (-3, 0, 4):
            with self.subTest(endpoint=endpoint):
                self.assertEqual(inclusive(endpoint, endpoint), [endpoint])

    def test_negative_endpoints_and_zero_crossing(self) -> None:
        cases = [
            (-4, -2, [-4, -3, -2]),
            (-2, -4, [-2, -3, -4]),
            (-2, 2, [-2, -1, 0, 1, 2]),
            (2, -2, [2, 1, 0, -1, -2]),
        ]
        for start, stop, expected in cases:
            with self.subTest(start=start, stop=stop):
                self.assertEqual(inclusive(start, stop), expected)


class InclusiveManyTests(unittest.TestCase):
    def test_many_preserves_case_order_and_inputs(self) -> None:
        cases = [(2, 4), (3, 1), (-1, -1), (-1, 1)]
        original = cases.copy()
        self.assertEqual(
            inclusive_many(cases),
            [[2, 3, 4], [3, 2, 1], [-1], [-1, 0, 1]],
        )
        self.assertEqual(cases, original)
        for case, saved in zip(cases, original):
            self.assertIs(case, saved)

    def test_many_empty(self) -> None:
        self.assertEqual(inclusive_many([]), [])

    def test_many_forwards_arguments_without_mutation(self) -> None:
        argument = [1, 2]
        cases = [(argument,)]
        with patch("solution.inclusive", return_value="result") as single:
            self.assertEqual(inclusive_many(cases), ["result"])
        single.assert_called_once_with(argument)
        self.assertIs(single.call_args.args[0], argument)
        self.assertEqual(argument, [1, 2])
        self.assertEqual(cases, [(argument,)])

    def test_many_propagates_first_exception_unchanged_and_stops(self) -> None:
        error = ValueError("first failure")
        cases = [(1, 2), (3, 4), (5, 6)]
        with patch("solution.inclusive", side_effect=[[1, 2], error]) as single:
            with self.assertRaises(ValueError) as raised:
                inclusive_many(cases)
        self.assertIs(raised.exception, error)
        self.assertEqual(single.call_args_list, [call(1, 2), call(3, 4)])
        self.assertEqual(cases, [(1, 2), (3, 4), (5, 6)])


if __name__ == "__main__":
    unittest.main()
