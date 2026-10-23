import unittest

from solution import prefix


class PrefixTests(unittest.TestCase):
    def test_ordinary_inputs(self) -> None:
        for items, expected in [
            ([1, 2, 3, 4], [1, 3, 6, 10]),
            ([-2, 5, -4, 0], [-2, 3, -1, -1]),
            ([-1, -2, -3], [-1, -3, -6]),
        ]:
            with self.subTest(items=items):
                original = items.copy()
                result = prefix(items)
                self.assertEqual(result, expected)
                self.assertEqual(len(result), len(items))
                self.assertEqual(items, original)
                self.assertIsNot(result, items)

    def test_boundary_inputs(self) -> None:
        for items, expected in [
            ([7], [7]),
            ([-7], [-7]),
            ([0, 0], [0, 0]),
            ([10**100, 1, -(10**100)], [10**100, 10**100 + 1, 1]),
        ]:
            with self.subTest(items=items):
                original = items.copy()
                self.assertEqual(prefix(items), expected)
                self.assertEqual(items, original)

    def test_empty_input(self) -> None:
        items: list[int] = []
        result = prefix(items)
        self.assertEqual(result, [])
        self.assertEqual(items, [])
        self.assertIsNot(result, items)


if __name__ == "__main__":
    unittest.main()
