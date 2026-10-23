"""Tests for the public inclusive API."""

import unittest

from solution import inclusive


class InclusiveTests(unittest.TestCase):
    def test_ascending(self) -> None:
        self.assertEqual(inclusive(2, 5), [2, 3, 4, 5])
        self.assertEqual(inclusive(-4, -2), [-4, -3, -2])

    def test_descending(self) -> None:
        self.assertEqual(inclusive(5, 2), [5, 4, 3, 2])
        self.assertEqual(inclusive(-2, -4), [-2, -3, -4])

    def test_equal_endpoints(self) -> None:
        for endpoint in (-7, 0, 7):
            with self.subTest(endpoint=endpoint):
                self.assertEqual(inclusive(endpoint, endpoint), [endpoint])

    def test_crossing_zero(self) -> None:
        self.assertEqual(inclusive(-2, 2), [-2, -1, 0, 1, 2])
        self.assertEqual(inclusive(2, -2), [2, 1, 0, -1, -2])

    def test_adjacent_endpoints(self) -> None:
        self.assertEqual(inclusive(-1, 0), [-1, 0])
        self.assertEqual(inclusive(0, -1), [0, -1])

    def test_large_integer_endpoints(self) -> None:
        for endpoint in (10**100, -(10**100)):
            with self.subTest(endpoint=endpoint):
                self.assertEqual(
                    inclusive(endpoint, endpoint + 2),
                    [endpoint, endpoint + 1, endpoint + 2],
                )
                self.assertEqual(
                    inclusive(endpoint + 2, endpoint),
                    [endpoint + 2, endpoint + 1, endpoint],
                )

    def test_invalid_numeric_endpoints(self) -> None:
        for invalid in (1.0, 1.5, float("nan"), float("inf"), 1 + 2j):
            for start, stop in ((invalid, 3), (1, invalid)):
                with self.subTest(start=start, stop=stop):
                    with self.assertRaises(TypeError):
                        inclusive(start, stop)


if __name__ == "__main__":
    unittest.main()
