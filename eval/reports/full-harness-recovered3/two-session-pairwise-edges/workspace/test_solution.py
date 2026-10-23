"""Public regression tests for adjacent pairs."""

import unittest
from unittest.mock import call, patch

from solution import pairs, pairs_many


class PairsTests(unittest.TestCase):
    def test_empty_input(self) -> None:
        self.assertEqual(pairs([]), [])

    def test_single_item(self) -> None:
        self.assertEqual(pairs([1]), [])

    def test_two_items(self) -> None:
        self.assertEqual(pairs([4, 2]), [(4, 2)])

    def test_overlapping_pairs_in_order(self) -> None:
        self.assertEqual(pairs([1, 2, 3]), [(1, 2), (2, 3)])

    def test_duplicates_and_negative_values(self) -> None:
        self.assertEqual(pairs([3, -1, -1, 0]), [(3, -1), (-1, -1), (-1, 0)])

    def test_input_is_unchanged(self) -> None:
        items = [1, 2, 3]
        original = items.copy()
        result = pairs(items)
        self.assertEqual(items, original)
        result.append((9, 10))
        self.assertEqual(items, original)


class PairsManyTests(unittest.TestCase):
    def test_batch_results_in_case_order_and_inputs_unchanged(self) -> None:
        cases = [([3, 1, 2],), ([],), ([7],), ([-1, -1],)]
        original_cases = cases.copy()
        original_items = [case[0].copy() for case in cases]

        results = pairs_many(cases)

        self.assertEqual(results, [[(3, 1), (1, 2)], [], [], [(-1, -1)]])
        self.assertEqual(cases, original_cases)
        for case, original_case, original in zip(cases, original_cases, original_items):
            self.assertIs(case, original_case)
            self.assertEqual(case[0], original)

    def test_empty_batch_does_not_call_pairs(self) -> None:
        with patch("solution.pairs") as mocked_pairs:
            self.assertEqual(pairs_many([]), [])
        mocked_pairs.assert_not_called()

    def test_each_case_is_unpacked_once(self) -> None:
        cases = [(1, 2), (), (3,)]
        with patch("solution.pairs", side_effect=["first", "second", "third"]) as mocked_pairs:
            self.assertEqual(pairs_many(cases), ["first", "second", "third"])
        self.assertEqual(mocked_pairs.call_args_list, [call(1, 2), call(), call(3)])

    def test_first_exception_is_propagated_unchanged(self) -> None:
        error = ValueError("failed case")
        cases = [([1, 2],), ([3, 4],), ([5, 6],)]
        with patch("solution.pairs", side_effect=[[(1, 2)], error]) as mocked_pairs:
            with self.assertRaises(ValueError) as caught:
                pairs_many(cases)
        self.assertIs(caught.exception, error)
        self.assertEqual(mocked_pairs.call_args_list, [call([1, 2]), call([3, 4])])


if __name__ == "__main__":
    unittest.main()
