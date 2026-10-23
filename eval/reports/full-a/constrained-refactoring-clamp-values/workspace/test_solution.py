import unittest

from solution import clamp, clamp_legacy


class ClampTests(unittest.TestCase):
    def test_inclusive_range(self):
        for function in (clamp, clamp_legacy):
            for value, expected in ((-5, 0), (0, 0), (4, 4), (10, 10), (15, 10)):
                with self.subTest(function=function.__name__, value=value):
                    result = function(value=value, low=0, high=10)
                    self.assertEqual(result, expected)
                    self.assertIs(type(result), int)

    def test_equal_bounds(self):
        for function in (clamp, clamp_legacy):
            for value in (-10, 3, 10):
                with self.subTest(function=function.__name__, value=value):
                    self.assertEqual(function(value, 3, 3), 3)

    def test_reversed_bounds(self):
        for function in (clamp, clamp_legacy):
            with self.subTest(function=function.__name__):
                with self.assertRaisesRegex(ValueError, '^reversed bounds$'):
                    function(5, 10, 0)

    def test_input_collections_are_unchanged(self):
        # Lists are comparable and were accepted by the original implementation.
        for function in (clamp, clamp_legacy):
            for value, expected in (([-1], [0]), ([5], [5]), ([11], [10])):
                low, high = [0], [10]
                originals = (value[:], low[:], high[:])
                with self.subTest(function=function.__name__, value=value):
                    self.assertEqual(function(value, low, high), expected)
                    self.assertEqual((value, low, high), originals)


if __name__ == '__main__':
    unittest.main()
