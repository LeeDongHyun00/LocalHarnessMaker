import unittest

from solution import inclusive, inclusive_legacy


class InclusiveTests(unittest.TestCase):
    def test_inclusive_ranges(self) -> None:
        cases = (
            (1, 4, [1, 2, 3, 4]),
            (4, 1, [4, 3, 2, 1]),
            (-2, 2, [-2, -1, 0, 1, 2]),
            (2, -2, [2, 1, 0, -1, -2]),
            (0, 0, [0]),
            (-3, -3, [-3]),
        )
        for function in (inclusive, inclusive_legacy):
            for start, stop, expected in cases:
                with self.subTest(function=function.__name__, start=start, stop=stop):
                    result = function(start=start, stop=stop)
                    self.assertIs(type(result), list)
                    self.assertEqual(result, expected)

    def test_invalid_inputs_raise_type_error(self) -> None:
        for function in (inclusive, inclusive_legacy):
            for start, stop in ((1.5, 3), (1, 3.5), (None, 3), ("1", "3")):
                with self.subTest(function=function.__name__, start=start, stop=stop):
                    with self.assertRaises(TypeError):
                        function(start, stop)

    def test_input_collections_are_not_mutated(self) -> None:
        for function in (inclusive, inclusive_legacy):
            start = [1, 2]
            stop = [3, 4]
            with self.subTest(function=function.__name__):
                with self.assertRaises(TypeError):
                    function(start, stop)
                self.assertEqual(start, [1, 2])
                self.assertEqual(stop, [3, 4])


if __name__ == "__main__":
    unittest.main()
