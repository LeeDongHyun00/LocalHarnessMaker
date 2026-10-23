import unittest

from solution import ordinal


class OrdinalTests(unittest.TestCase):
    def test_regular_suffixes(self):
        for value, expected in (
            (1, '1st'), (2, '2nd'), (3, '3rd'), (4, '4th'),
            (10, '10th'), (21, '21st'), (22, '22nd'), (23, '23rd'),
            (24, '24th'), (101, '101st'), (102, '102nd'), (103, '103rd'),
        ):
            with self.subTest(value=value):
                self.assertEqual(ordinal(value), expected)

    def test_teen_exceptions(self):
        for value in (11, 12, 13, 111, 112, 113, 1011, 1012, 1013):
            with self.subTest(value=value):
                self.assertEqual(ordinal(value), f'{value}th')

    def test_zero(self):
        self.assertEqual(ordinal(0), '0th')

    def test_negatives_raise_value_error(self):
        for value in (-1, -2, -11, -112, -1000):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    ordinal(value)

    def test_input_values_and_collection_order_are_preserved(self):
        values = [23, 0, 111, 1, 23, 12, 2]
        original = values.copy()
        self.assertEqual(
            [ordinal(value) for value in values],
            ['23rd', '0th', '111th', '1st', '23rd', '12th', '2nd'],
        )
        self.assertEqual(values, original)


if __name__ == '__main__':
    unittest.main()
