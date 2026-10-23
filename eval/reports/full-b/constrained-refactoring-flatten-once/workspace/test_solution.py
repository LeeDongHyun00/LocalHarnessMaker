"""Tests for the public flattening functions."""

import unittest

from solution import flatten, flatten_legacy


class FlattenTests(unittest.TestCase):
    def test_preserves_order_and_ignores_empty_groups(self):
        for function in (flatten, flatten_legacy):
            with self.subTest(function=function.__name__):
                self.assertEqual(
                    function([[], [3, 1], [], [2, 2], []]),
                    [3, 1, 2, 2],
                )

    def test_flattens_exactly_one_level(self):
        for function in (flatten, flatten_legacy):
            with self.subTest(function=function.__name__):
                nested = [1, 2]
                result = function([[nested], [3]])
                self.assertEqual(result, [[1, 2], 3])
                self.assertIs(result[0], nested)

    def test_returns_new_list_without_mutating_inputs(self):
        for function in (flatten, flatten_legacy):
            with self.subTest(function=function.__name__):
                first = [1, 2]
                second = [3]
                items = [first, [], second, first]

                result = function(items)

                self.assertIs(type(result), list)
                self.assertIsNot(result, items)
                for group in items:
                    self.assertIsNot(result, group)
                self.assertEqual(result, [1, 2, 3, 1, 2])
                self.assertEqual(items, [[1, 2], [], [3], [1, 2]])
                self.assertIs(items[0], first)
                self.assertIs(items[2], second)
                self.assertIs(items[3], first)

                result.append(4)
                self.assertEqual(first, [1, 2])
                self.assertEqual(second, [3])

    def test_empty_inputs_produce_fresh_lists(self):
        for function in (flatten, flatten_legacy):
            for items in ([], [[], []]):
                with self.subTest(function=function.__name__, items=items):
                    result = function(items)
                    self.assertEqual(result, [])
                    self.assertIs(type(result), list)
                    self.assertIsNot(result, items)
                    self.assertIsNot(result, function(items))
                    for group in items:
                        self.assertIsNot(result, group)

    def test_invalid_inputs_preserve_type_errors_and_inputs(self):
        cases = (
            (None, "'NoneType' object is not iterable"),
            (1, "'int' object is not iterable"),
            ([1], "'int' object is not iterable"),
            ([[1, 2], None], "'NoneType' object is not iterable"),
        )
        for function in (flatten, flatten_legacy):
            for items, message in cases:
                with self.subTest(function=function.__name__, items=items):
                    with self.assertRaises(TypeError) as error:
                        function(items)
                    self.assertEqual(str(error.exception), message)
            self.assertEqual(cases[-1][0], [[1, 2], None])


if __name__ == "__main__":
    unittest.main()
