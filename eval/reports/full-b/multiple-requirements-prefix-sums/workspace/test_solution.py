import unittest

from solution import prefix


class PrefixTests(unittest.TestCase):
    def test_inclusive_sums_follow_input_order(self) -> None:
        self.assertEqual(prefix([3, 1, 4, 1, 5]), [3, 4, 8, 9, 14])

    def test_empty_input(self) -> None:
        self.assertEqual(prefix([]), [])

    def test_single_element(self) -> None:
        for value in (7, -3, 0):
            with self.subTest(value=value):
                self.assertEqual(prefix([value]), [value])

    def test_negative_numbers_and_zeros(self) -> None:
        cases = (
            ([-2, -3, -1], [-2, -5, -6]),
            ([4, -6, 0, 5, -3], [4, -2, -2, 3, 0]),
            ([0, 0, 0], [0, 0, 0]),
        )
        for items, expected in cases:
            with self.subTest(items=items):
                self.assertEqual(prefix(items), expected)

    def test_input_values_and_order_are_preserved(self) -> None:
        items = [5, -2, 5, 0, -7]
        original = items.copy()

        result = prefix(items)

        self.assertEqual(result, [5, 3, 8, 8, 1])
        self.assertEqual(len(result), len(items))
        self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
