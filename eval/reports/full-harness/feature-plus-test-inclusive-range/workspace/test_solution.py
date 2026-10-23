"""Tests for the public inclusive integer range API."""

import unittest

from solution import inclusive


class InclusiveTests(unittest.TestCase):
    def test_ascending(self):
        self.assertEqual(inclusive(2, 5), [2, 3, 4, 5])

    def test_descending(self):
        self.assertEqual(inclusive(5, 2), [5, 4, 3, 2])

    def test_equal_endpoints(self):
        for endpoint in (-3, 0, 4):
            with self.subTest(endpoint=endpoint):
                self.assertEqual(inclusive(endpoint, endpoint), [endpoint])

    def test_negative_and_zero_boundaries(self):
        self.assertEqual(inclusive(-3, -1), [-3, -2, -1])
        self.assertEqual(inclusive(-1, 1), [-1, 0, 1])
        self.assertEqual(inclusive(1, -1), [1, 0, -1])
        self.assertEqual(inclusive(0, 1), [0, 1])
        self.assertEqual(inclusive(0, -1), [0, -1])

    def test_large_integer_endpoints(self):
        endpoint = 10**30
        self.assertEqual(inclusive(endpoint, endpoint + 1), [endpoint, endpoint + 1])
        self.assertEqual(inclusive(-endpoint, -endpoint - 1), [-endpoint, -endpoint - 1])

    def test_invalid_numeric_inputs(self):
        for start, stop in ((1.5, 3), (1, 3.5), (float("nan"), 3), (1, float("inf"))):
            with self.subTest(start=start, stop=stop):
                with self.assertRaises(TypeError):
                    inclusive(start, stop)


if __name__ == "__main__":
    unittest.main()
