"""Regression tests for the public inclusive API."""

import unittest

from solution import inclusive


class InclusiveTests(unittest.TestCase):
    def test_ascending_includes_both_endpoints(self) -> None:
        self.assertEqual(inclusive(2, 5), [2, 3, 4, 5])

    def test_descending_preserves_traversal_order(self) -> None:
        self.assertEqual(inclusive(5, 2), [5, 4, 3, 2])

    def test_equal_endpoints_return_singleton(self) -> None:
        for endpoint in (-3, 0, 4):
            with self.subTest(endpoint=endpoint):
                self.assertEqual(inclusive(endpoint, endpoint), [endpoint])

    def test_negative_endpoints_and_crossing_zero(self) -> None:
        for start, stop, expected in (
            (-4, -2, [-4, -3, -2]),
            (-2, -4, [-2, -3, -4]),
            (-2, 2, [-2, -1, 0, 1, 2]),
            (2, -2, [2, 1, 0, -1, -2]),
        ):
            with self.subTest(start=start, stop=stop):
                self.assertEqual(inclusive(start, stop), expected)

    def test_input_collection_values_and_order_are_preserved(self) -> None:
        endpoints = [3, -1]
        original = endpoints.copy()
        result = inclusive(*endpoints)
        self.assertEqual(result, [3, 2, 1, 0, -1])
        self.assertEqual(endpoints, original)
        result.append(99)
        self.assertEqual(endpoints, original)
        self.assertEqual(inclusive(*endpoints), [3, 2, 1, 0, -1])


if __name__ == "__main__":
    unittest.main()
