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

    def test_ranges_cross_zero_in_both_directions(self) -> None:
        self.assertEqual(inclusive(-2, 2), [-2, -1, 0, 1, 2])
        self.assertEqual(inclusive(2, -2), [2, 1, 0, -1, -2])

    def test_input_collection_values_and_order_are_preserved(self) -> None:
        endpoints = [4, -2]
        self.assertEqual(inclusive(*endpoints), [4, 3, 2, 1, 0, -1, -2])
        self.assertEqual(endpoints, [4, -2])


if __name__ == "__main__":
    unittest.main()
