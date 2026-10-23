"""Tests for the public inclusive API."""

import unittest

from solution import inclusive


class InclusiveTests(unittest.TestCase):
    def test_ordinary_ranges(self) -> None:
        cases = [
            (2, 5, [2, 3, 4, 5]),
            (5, 2, [5, 4, 3, 2]),
            (-4, -2, [-4, -3, -2]),
            (-2, -4, [-2, -3, -4]),
            (-2, 2, [-2, -1, 0, 1, 2]),
            (2, -2, [2, 1, 0, -1, -2]),
        ]
        for start, stop, expected in cases:
            with self.subTest(start=start, stop=stop):
                self.assertEqual(inclusive(start, stop), expected)

    def test_equal_endpoints(self) -> None:
        for endpoint in (-5, 0, 5, 10**30):
            with self.subTest(endpoint=endpoint):
                self.assertEqual(inclusive(endpoint, endpoint), [endpoint])

    def test_adjacent_endpoints(self) -> None:
        self.assertEqual(inclusive(0, 1), [0, 1])
        self.assertEqual(inclusive(0, -1), [0, -1])

    def test_invalid_numeric_inputs(self) -> None:
        for start, stop in ((1.5, 3), (1, 3.5), (float("nan"), 1),
                            (1, float("inf")), (1 + 2j, 3)):
            with self.subTest(start=start, stop=stop):
                with self.assertRaises(TypeError):
                    inclusive(start, stop)


if __name__ == "__main__":
    unittest.main()
