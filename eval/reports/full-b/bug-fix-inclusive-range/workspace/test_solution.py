import unittest

from solution import inclusive


class InclusiveTests(unittest.TestCase):
    def test_inclusive_endpoint_orders(self) -> None:
        cases = [
            (-2, 2, [-2, -1, 0, 1, 2]),
            (2, -2, [2, 1, 0, -1, -2]),
            (0, 0, [0]),
        ]
        for start, stop, expected in cases:
            with self.subTest(start=start, stop=stop):
                self.assertEqual(inclusive(start, stop), expected)


if __name__ == "__main__":
    unittest.main()
