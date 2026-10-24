import unittest

from solution import prefix


class PrefixTests(unittest.TestCase):
    def test_inclusive_prefix_sums(self) -> None:
        for items, expected in [
            ([1, 2, 3], [1, 3, 6]),
            ([3, -5, 4, -2], [3, -2, 2, 0]),
            ([-4], [-4]),
            ([], []),
        ]:
            with self.subTest(items=items):
                original = items.copy()
                result = prefix(items)
                self.assertEqual(result, expected)
                self.assertEqual(len(result), len(items))
                self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
