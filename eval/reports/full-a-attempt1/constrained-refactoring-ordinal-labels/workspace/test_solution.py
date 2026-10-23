import unittest

from solution import ordinal, ordinal_legacy


class OrdinalTests(unittest.TestCase):
    def test_suffixes(self) -> None:
        cases = {
            0: '0th', 1: '1st', 2: '2nd', 3: '3rd', 4: '4th',
            10: '10th', 11: '11th', 12: '12th', 13: '13th',
            14: '14th', 19: '19th', 20: '20th', 21: '21st',
            22: '22nd', 23: '23rd', 24: '24th', 100: '100th',
            101: '101st', 102: '102nd', 103: '103rd',
            111: '111th', 112: '112th', 113: '113th', 121: '121st',
        }
        for function in (ordinal, ordinal_legacy):
            for value, expected in cases.items():
                with self.subTest(function=function.__name__, value=value):
                    result = function(value)
                    self.assertIsInstance(result, str)
                    self.assertEqual(result, expected)

    def test_negative_values(self) -> None:
        for function in (ordinal, ordinal_legacy):
            for value in (-1, -13, -1000):
                with self.subTest(function=function.__name__, value=value):
                    with self.assertRaisesRegex(
                        ValueError, '^nonnegative value required$'
                    ):
                        function(value)

    def test_input_collection_is_unchanged(self) -> None:
        values = [0, 1, 2, 3, 11, 12, 13, 111, 112, 113]
        original = values.copy()
        for function in (ordinal, ordinal_legacy):
            with self.subTest(function=function.__name__):
                results = [function(value) for value in values]
                self.assertEqual(len(results), len(values))
                self.assertEqual(values, original)


if __name__ == '__main__':
    unittest.main()
