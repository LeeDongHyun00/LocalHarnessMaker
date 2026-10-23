import unittest

from solution import prefix


class PrefixTests(unittest.TestCase):
    def test_inclusive_sums_preserve_length_and_order(self) -> None:
        items = [4, 1, 7, 2]
        result = prefix(items)
        self.assertEqual(result, [4, 5, 12, 14])
        self.assertEqual(len(result), len(items))

    def test_empty_input(self) -> None:
        items: list[int] = []
        result = prefix(items)
        self.assertEqual(result, [])
        self.assertIsNot(result, items)

    def test_single_element(self) -> None:
        self.assertEqual(prefix([9]), [9])

    def test_negative_numbers_and_zero(self) -> None:
        self.assertEqual(prefix([-3, 0, 5, -7]), [-3, -3, 2, -5])

    def test_input_values_and_order_are_unchanged(self) -> None:
        items = [5, -2, 0, 5, -8]
        original = items.copy()
        result = prefix(items)
        self.assertEqual(items, original)
        self.assertIsNot(result, items)
        result[0] = 100
        self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
