import unittest

from solution import ordinal


class OrdinalTests(unittest.TestCase):
    def test_zero_and_regular_suffixes(self) -> None:
        cases = {
            0: "0th", 1: "1st", 2: "2nd", 3: "3rd", 4: "4th",
            10: "10th", 21: "21st", 22: "22nd", 23: "23rd",
            24: "24th", 100: "100th", 101: "101st", 102: "102nd",
            103: "103rd",
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(ordinal(value), expected)

    def test_teen_suffix_exceptions_repeat_every_hundred(self) -> None:
        for value in (11, 12, 13, 111, 112, 113, 1011, 1012, 1013):
            with self.subTest(value=value):
                self.assertEqual(ordinal(value), f"{value}th")

    def test_negative_values_raise_value_error(self) -> None:
        for value in (-1, -2, -11, -100, -(10 ** 100)):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    ordinal(value)

    def test_preserves_input_values_and_collection_order(self) -> None:
        values = [113, 2, 0, 21, 2, 11, 3]
        original = values.copy()
        self.assertEqual(
            list(map(ordinal, values)),
            ["113th", "2nd", "0th", "21st", "2nd", "11th", "3rd"],
        )
        self.assertEqual(values, original)

    def test_large_integers(self) -> None:
        for ending, suffix in ((1, "st"), (2, "nd"), (3, "rd"), (11, "th")):
            value = 10 ** 100 + ending
            with self.subTest(value=value):
                self.assertEqual(ordinal(value), f"{value}{suffix}")


if __name__ == "__main__":
    unittest.main()
