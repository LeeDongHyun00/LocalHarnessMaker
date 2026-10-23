"""Regression coverage for the public pairs API."""

import unittest
from unittest.mock import call, patch

from solution import pairs, pairs_many


class PairsTests(unittest.TestCase):
    def test_overlapping_pairs_preserve_order(self) -> None:
        self.assertEqual(pairs([1, 2, 3, 4]), [(1, 2), (2, 3), (3, 4)])

    def test_short_inputs_return_empty_list(self) -> None:
        for items in ([], [7]):
            with self.subTest(items=items):
                self.assertEqual(pairs(items), [])

    def test_two_items_return_one_pair(self) -> None:
        self.assertEqual(pairs([5, -2]), [(5, -2)])

    def test_duplicates_and_negative_values(self) -> None:
        self.assertEqual(pairs([-1, -1, 0, -3]), [(-1, -1), (-1, 0), (0, -3)])

    def test_input_is_not_mutated(self) -> None:
        items = [3, 1, 2]
        original = items.copy()
        result = pairs(items)
        self.assertEqual(items, original)
        self.assertEqual(result, [(3, 1), (1, 2)])
        result.append((9, 10))
        self.assertEqual(items, original)


class PairsManyTests(unittest.TestCase):
    def test_batch_results_follow_case_order(self) -> None:
        cases = [([1, 2, 3],), ([],), ([7],), ([-2, 5],)]
        self.assertEqual(
            pairs_many(cases),
            [[(1, 2), (2, 3)], [], [], [(-2, 5)]],
        )

    def test_empty_batch_does_not_call_pairs(self) -> None:
        with patch("solution.pairs") as pairs_mock:
            self.assertEqual(pairs_many([]), [])
        pairs_mock.assert_not_called()

    def test_batch_does_not_mutate_cases_or_shared_arguments(self) -> None:
        items = [3, 1, 2]
        cases = [(items,), (items,)]
        original_cases = cases.copy()
        results = pairs_many(cases)
        self.assertEqual(cases, original_cases)
        self.assertIs(cases[0], original_cases[0])
        self.assertIs(cases[1], original_cases[1])
        self.assertIs(cases[0][0], items)
        self.assertEqual(items, [3, 1, 2])
        results[0].append((9, 10))
        self.assertEqual(results[1], [(3, 1), (1, 2)])
        self.assertEqual(items, [3, 1, 2])

    def test_first_exception_is_propagated_unchanged_and_stops_batch(self) -> None:
        error = ValueError("first failure")
        cases = [([1, 2],), ([3, 4],), ([5, 6],)]
        with patch("solution.pairs", side_effect=[[(1, 2)], error, []]) as mock:
            with self.assertRaises(ValueError) as caught:
                pairs_many(cases)
        self.assertIs(caught.exception, error)
        self.assertEqual(mock.call_args_list, [call([1, 2]), call([3, 4])])

    def test_each_tuple_is_unpacked_as_positional_arguments(self) -> None:
        cases = [(), ([1], [2])]
        with patch("solution.pairs", side_effect=["zero", "two"]) as mock:
            self.assertEqual(pairs_many(cases), ["zero", "two"])
        self.assertEqual(mock.call_args_list, [call(), call([1], [2])])

    def test_invalid_arity_raises_type_error(self) -> None:
        for case in ((), ([1], [2])):
            with self.subTest(case=case):
                with self.assertRaises(TypeError):
                    pairs_many([case])


if __name__ == "__main__":
    unittest.main()
