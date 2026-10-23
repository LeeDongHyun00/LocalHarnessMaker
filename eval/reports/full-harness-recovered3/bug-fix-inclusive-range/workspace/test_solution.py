import unittest

from solution import inclusive


class InclusiveTests(unittest.TestCase):
    def test_includes_both_endpoints_in_either_direction(self) -> None:
        cases = [
            (1, 3, [1, 2, 3]),
            (3, 1, [3, 2, 1]),
            (2, 2, [2]),
            (-2, 1, [-2, -1, 0, 1]),
            (1, -2, [1, 0, -1, -2]),
        ]
        for start, stop, expected in cases:
            with self.subTest(start=start, stop=stop):
                self.assertEqual(inclusive(start, stop), expected)


if __name__ == "__main__":
    unittest.main()
