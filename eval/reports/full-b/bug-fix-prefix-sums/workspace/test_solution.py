import unittest

from solution import prefix


class PrefixTests(unittest.TestCase):
    def test_inclusive_prefix_sums(self) -> None:
        cases = [
            ([], []),
            ([4], [4]),
            ([1, 2, 3], [1, 3, 6]),
            ([3, -5, 2, -1], [3, -2, 0, -1]),
        ]
        for items, expected in cases:
            with self.subTest(items=items):
                original = items.copy()
                self.assertEqual(prefix(items), expected)
                self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
