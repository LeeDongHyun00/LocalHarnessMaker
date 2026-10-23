import unittest
from copy import deepcopy

from solution import inclusive, inclusive_legacy


class InclusiveTests(unittest.TestCase):
    def test_inclusive_ranges(self):
        cases = [
            (1, 4, [1, 2, 3, 4]),
            (4, 1, [4, 3, 2, 1]),
            (0, 0, [0]),
            (-3, -3, [-3]),
            (-3, -1, [-3, -2, -1]),
            (-1, -3, [-1, -2, -3]),
            (-2, 2, [-2, -1, 0, 1, 2]),
            (2, -2, [2, 1, 0, -1, -2]),
            (10**30, 10**30 + 1, [10**30, 10**30 + 1]),
            (True, False, [1, 0]),
        ]
        for function in (inclusive, inclusive_legacy):
            for start, stop, expected in cases:
                with self.subTest(function=function.__name__, start=start, stop=stop):
                    result = function(start=start, stop=stop)
                    self.assertIs(type(result), list)
                    self.assertEqual(result, expected)
                    self.assertTrue(all(type(value) is int for value in result))

    def test_results_are_independent_lists(self):
        for function in (inclusive, inclusive_legacy):
            with self.subTest(function=function.__name__):
                first = function(1, 3)
                second = function(1, 3)
                self.assertIsNot(first, second)
                first.append(4)
                self.assertEqual(second, [1, 2, 3])

    def test_invalid_endpoints_raise_type_error(self):
        cases = [(None, 3), (1, None), (1.5, 3), (1, 3.5), ("1", "3")]
        for function in (inclusive, inclusive_legacy):
            for start, stop in cases:
                with self.subTest(function=function.__name__, start=start, stop=stop):
                    with self.assertRaises(TypeError):
                        function(start, stop)

    def test_input_collections_are_not_mutated_on_error(self):
        cases = [
            ([1, 2], [3, 4]),
            ({"value": 1}, {"value": 3}),
            ({1, 2}, {3, 4}),
        ]
        for function in (inclusive, inclusive_legacy):
            for start, stop in cases:
                with self.subTest(function=function.__name__, start=start, stop=stop):
                    original_start, original_stop = deepcopy((start, stop))
                    with self.assertRaises(TypeError):
                        function(start, stop)
                    self.assertEqual(start, original_start)
                    self.assertEqual(stop, original_stop)


if __name__ == "__main__":
    unittest.main()
