"""Regression coverage for the public flatten API."""

import unittest
from unittest.mock import call, patch

from solution import flatten, flatten_many


class FlattenTests(unittest.TestCase):
    def test_preserves_order_and_duplicates(self) -> None:
        self.assertEqual(flatten([[3, 1], [3], [-2, 0]]), [3, 1, 3, -2, 0])

    def test_ignores_empty_inner_lists(self) -> None:
        self.assertEqual(flatten([[], [1, 2], [], [3], []]), [1, 2, 3])

    def test_empty_inputs_return_new_lists(self) -> None:
        items: list[list[int]] = []
        result = flatten(items)
        self.assertEqual(result, [])
        self.assertIsNot(result, items)
        self.assertEqual(flatten([[], []]), [])
        self.assertIsNot(result, flatten(items))

    def test_does_not_mutate_or_reuse_input_lists(self) -> None:
        inner = [1, 2]
        items = [inner, [], inner]
        original_inners = items.copy()
        result = flatten(items)
        self.assertEqual(result, [1, 2, 1, 2])
        self.assertEqual(items, [[1, 2], [], [1, 2]])
        for actual, original in zip(items, original_inners):
            self.assertIs(actual, original)
            self.assertIsNot(result, actual)
        result.append(9)
        self.assertEqual(items, [[1, 2], [], [1, 2]])
        inner.append(3)
        self.assertEqual(result, [1, 2, 1, 2, 9])


class FlattenManyTests(unittest.TestCase):
    def test_batch_preserves_case_and_element_order(self) -> None:
        cases = [([[3, 1], [], [3]],), ([],), ([[-2], [0, 4]],)]
        self.assertEqual(flatten_many(cases), [[3, 1, 3], [], [-2, 0, 4]])

    def test_empty_batch_returns_fresh_list_without_calls(self) -> None:
        cases = []
        with patch("solution.flatten") as single:
            result = flatten_many(cases)
            self.assertEqual(result, [])
            self.assertIsNot(result, cases)
            self.assertIsNot(result, flatten_many(cases))
            single.assert_not_called()

    def test_batch_preserves_inputs_and_returns_independent_results(self) -> None:
        inner = [1, 2]
        items = [inner, [], inner]
        case = (items,)
        cases = [case, case]
        result = flatten_many(cases)
        self.assertEqual(result, [[1, 2, 1, 2], [1, 2, 1, 2]])
        self.assertEqual(cases, [([[1, 2], [], [1, 2]],)] * 2)
        self.assertTrue(all(actual is case for actual in cases))
        self.assertIs(case[0], items)
        self.assertIs(items[0], inner)
        self.assertIs(items[2], inner)
        self.assertIsNot(result[0], result[1])
        result[0].append(9)
        self.assertEqual(result[1], [1, 2, 1, 2])
        self.assertEqual(items, [[1, 2], [], [1, 2]])
        inner.append(3)
        self.assertEqual(result, [[1, 2, 1, 2, 9], [1, 2, 1, 2]])

    def test_forwards_positional_arguments_and_first_exception_unchanged(self) -> None:
        first_error = RuntimeError("first failure")
        later_error = ValueError("later failure")
        cases = [(object(),), (), (object(), object())]
        with patch("solution.flatten", side_effect=[[], first_error, later_error]) as single:
            with self.assertRaises(RuntimeError) as raised:
                flatten_many(cases)
            self.assertIs(raised.exception, first_error)
            self.assertEqual(single.call_args_list, [call(*cases[0]), call()])

    def test_invalid_argument_counts_propagate_type_error(self) -> None:
        for invalid_case in [(), ([], [])]:
            with self.subTest(case=invalid_case):
                with self.assertRaises(TypeError):
                    flatten_many([([[1]],), invalid_case])


if __name__ == "__main__":
    unittest.main()
