import unittest

from solution import inclusive, inclusive_legacy


class InclusiveTests(unittest.TestCase):
    def test_ranges_in_both_directions(self):
        for function in (inclusive, inclusive_legacy):
            for start, stop, expected in (
                (-2, 2, [-2, -1, 0, 1, 2]),
                (2, -2, [2, 1, 0, -1, -2]),
                (3, 5, [3, 4, 5]),
            ):
                with self.subTest(function=function.__name__, start=start, stop=stop):
                    result = function(start=start, stop=stop)
                    self.assertIsInstance(result, list)
                    self.assertEqual(result, expected)

    def test_equal_endpoints(self):
        for function in (inclusive, inclusive_legacy):
            for endpoint in (-3, 0, 4):
                with self.subTest(function=function.__name__, endpoint=endpoint):
                    self.assertEqual(function(endpoint, endpoint), [endpoint])

    def test_invalid_inputs_raise_type_error(self):
        for function in (inclusive, inclusive_legacy):
            for start, stop in ((1.5, 3), (1, 3.5), (None, 3), (1, "3")):
                with self.subTest(function=function.__name__, start=start, stop=stop):
                    with self.assertRaises(TypeError):
                        function(start, stop)

    def test_invalid_collections_are_not_mutated(self):
        for function in (inclusive, inclusive_legacy):
            start = [1]
            stop = [3]
            with self.subTest(function=function.__name__):
                with self.assertRaises(TypeError):
                    function(start, stop)
                self.assertEqual(start, [1])
                self.assertEqual(stop, [3])


if __name__ == "__main__":
    unittest.main()
