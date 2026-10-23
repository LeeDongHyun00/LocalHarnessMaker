import unittest

from solution import inclusive


class InclusiveTests(unittest.TestCase):
    def test_inclusive_endpoints_and_direction(self) -> None:
        for start, stop, expected in (
            (1, 3, [1, 2, 3]),
            (3, 1, [3, 2, 1]),
            (2, 2, [2]),
            (-2, 1, [-2, -1, 0, 1]),
            (1, -2, [1, 0, -1, -2]),
        ):
            with self.subTest(start=start, stop=stop):
                self.assertEqual(inclusive(start, stop), expected)


if __name__ == "__main__":
    unittest.main()
