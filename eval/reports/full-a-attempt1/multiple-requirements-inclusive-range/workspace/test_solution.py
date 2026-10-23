import unittest

from solution import inclusive


class InclusiveTests(unittest.TestCase):
    def test_ascending_includes_both_endpoints(self) -> None:
        self.assertEqual(inclusive(2, 5), [2, 3, 4, 5])

    def test_descending_preserves_traversal_order(self) -> None:
        self.assertEqual(inclusive(5, 2), [5, 4, 3, 2])

    def test_equal_endpoints_produce_singleton(self) -> None:
        for endpoint in (-3, 0, 4):
            with self.subTest(endpoint=endpoint):
                self.assertEqual(inclusive(endpoint, endpoint), [endpoint])

    def test_negative_endpoints_and_crossing_zero(self) -> None:
        self.assertEqual(inclusive(-3, -1), [-3, -2, -1])
        self.assertEqual(inclusive(-2, 2), [-2, -1, 0, 1, 2])
        self.assertEqual(inclusive(2, -2), [2, 1, 0, -1, -2])

    def test_input_values_and_collection_order_are_preserved(self) -> None:
        endpoints = [3, -1]
        original = endpoints.copy()
        self.assertEqual(inclusive(*endpoints), [3, 2, 1, 0, -1])
        self.assertEqual(endpoints, original)

    def test_results_are_independent_lists(self) -> None:
        first = inclusive(1, 2)
        first.append(99)
        self.assertEqual(inclusive(1, 2), [1, 2])


if __name__ == "__main__":
    unittest.main()
