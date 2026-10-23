import unittest

from solution import prefix


class PrefixTests(unittest.TestCase):
    def test_ordinary_inputs(self):
        for items, expected in [
            ([1, 2, 3, 4], [1, 3, 6, 10]),
            ([-3, 5, -4, 0], [-3, 2, -2, -2]),
            ([-1, -2, -3], [-1, -3, -6]),
        ]:
            with self.subTest(items=items):
                original = items.copy()
                result = prefix(items)
                self.assertEqual(result, expected)
                self.assertEqual(len(result), len(items))
                self.assertEqual(items, original)
                self.assertIsNot(result, items)

    def test_boundary_inputs(self):
        for items in [[0], [7], [-7], [0, 0], [10**100, -10**100]]:
            with self.subTest(items=items):
                original = items.copy()
                result = prefix(items)
                self.assertEqual(
                    result, [sum(items[:end]) for end in range(1, len(items) + 1)]
                )
                self.assertEqual(len(result), len(items))
                self.assertEqual(items, original)

    def test_empty_input(self):
        items: list[int] = []
        result = prefix(items)
        self.assertEqual(result, [])
        self.assertEqual(items, [])
        self.assertIsNot(result, items)


if __name__ == "__main__":
    unittest.main()
