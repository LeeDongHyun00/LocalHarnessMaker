"""Regression tests for the public inclusive API."""

import unittest
from unittest.mock import call, patch

from solution import inclusive, inclusive_many


class InclusiveTests(unittest.TestCase):
    def test_ascending_includes_both_endpoints(self) -> None:
        self.assertEqual(inclusive(2, 5), [2, 3, 4, 5])

    def test_descending_includes_both_endpoints(self) -> None:
        self.assertEqual(inclusive(5, 2), [5, 4, 3, 2])

    def test_equal_endpoints_produce_singleton(self) -> None:
        for endpoint in (-3, 0, 4):
            with self.subTest(endpoint=endpoint):
                self.assertEqual(inclusive(endpoint, endpoint), [endpoint])

    def test_ranges_crossing_zero(self) -> None:
        self.assertEqual(inclusive(-2, 2), [-2, -1, 0, 1, 2])
        self.assertEqual(inclusive(2, -2), [2, 1, 0, -1, -2])

    def test_negative_endpoints(self) -> None:
        self.assertEqual(inclusive(-4, -2), [-4, -3, -2])
        self.assertEqual(inclusive(-2, -4), [-2, -3, -4])


class InclusiveManyTests(unittest.TestCase):
    def test_batch_preserves_order_and_cases(self) -> None:
        cases = [(2, 4), (3, 1), (-1, -1), (-2, 0)]
        original = cases.copy()
        self.assertEqual(
            inclusive_many(cases),
            [[2, 3, 4], [3, 2, 1], [-1], [-2, -1, 0]],
        )
        self.assertEqual(cases, original)
        for case, saved in zip(cases, original):
            self.assertIs(case, saved)

    def test_empty_batch(self) -> None:
        with patch("solution.inclusive") as single:
            self.assertEqual(inclusive_many([]), [])
        single.assert_not_called()

    def test_forwards_arguments_without_mutation(self) -> None:
        first, second = [1, 2], {"value": 3}
        cases = [(first, second)]
        with patch("solution.inclusive", return_value=[7]) as single:
            self.assertEqual(inclusive_many(cases), [[7]])
        self.assertIs(single.call_args.args[0], first)
        self.assertIs(single.call_args.args[1], second)
        self.assertEqual(cases, [([1, 2], {"value": 3})])

    def test_first_exception_is_propagated_unchanged(self) -> None:
        error = ValueError("first failure")
        cases = [(1, 2), (3, 4), (5, 6)]
        with patch("solution.inclusive", side_effect=[[1, 2], error]) as single:
            with self.assertRaises(ValueError) as raised:
                inclusive_many(cases)
        self.assertIs(raised.exception, error)
        self.assertEqual(single.call_args_list, [call(1, 2), call(3, 4)])
        self.assertEqual(cases, [(1, 2), (3, 4), (5, 6)])

    def test_invalid_arguments_raise_type_error(self) -> None:
        for case in [(), (1,), (1, 2, 3), ("a", "b")]:
            with self.subTest(case=case):
                with self.assertRaises(TypeError):
                    inclusive_many([case])


if __name__ == "__main__":
    unittest.main()
