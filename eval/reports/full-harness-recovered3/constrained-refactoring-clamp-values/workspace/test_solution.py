import unittest

from solution import clamp, clamp_legacy


class ClampTests(unittest.TestCase):
    def test_inclusive_range(self):
        for function in (clamp, clamp_legacy):
            for value, expected in ((-5, -2), (-2, -2), (0, 0), (3, 3), (8, 3)):
                with self.subTest(function=function.__name__, value=value):
                    result = function(value, -2, 3)
                    self.assertEqual(result, expected)
                    self.assertIs(type(result), int)

    def test_equal_bounds(self):
        for function in (clamp, clamp_legacy):
            for value in (-1, 4, 9):
                with self.subTest(function=function.__name__, value=value):
                    self.assertEqual(function(value, 4, 4), 4)

    def test_reversed_bounds(self):
        for function in (clamp, clamp_legacy):
            with self.subTest(function=function.__name__):
                with self.assertRaisesRegex(ValueError, '^reversed bounds$'):
                    function(0, 3, -2)

    def test_collection_inputs_are_not_mutated(self):
        for function in (clamp, clamp_legacy):
            for item, selected in ((0, 1), (2, 0), (4, 2)):
                with self.subTest(function=function.__name__, item=item):
                    inputs = ([item], [1], [3])
                    snapshots = tuple(value.copy() for value in inputs)
                    result = function(*inputs)
                    self.assertIs(result, inputs[selected])
                    self.assertEqual(inputs, snapshots)


if __name__ == '__main__':
    unittest.main()
