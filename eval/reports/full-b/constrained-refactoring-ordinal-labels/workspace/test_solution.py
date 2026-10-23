"""Tests for the public ordinal formatters."""

import copy
import inspect
import unittest

from solution import ordinal, ordinal_legacy


class OrdinalTests(unittest.TestCase):
    def test_suffixes_and_string_return_type(self) -> None:
        cases = {
            0: '0th',
            1: '1st',
            2: '2nd',
            3: '3rd',
            4: '4th',
            9: '9th',
            10: '10th',
            11: '11th',
            12: '12th',
            13: '13th',
            14: '14th',
            19: '19th',
            20: '20th',
            21: '21st',
            22: '22nd',
            23: '23rd',
            24: '24th',
            100: '100th',
            101: '101st',
            102: '102nd',
            103: '103rd',
            110: '110th',
            111: '111th',
            112: '112th',
            113: '113th',
            114: '114th',
            120: '120th',
            121: '121st',
            122: '122nd',
            123: '123rd',
            1011: '1011th',
            1012: '1012th',
            1013: '1013th',
            10**100 + 1: str(10**100 + 1) + 'st',
        }
        original = cases.copy()
        for formatter in (ordinal, ordinal_legacy):
            for value, expected in cases.items():
                with self.subTest(formatter=formatter.__name__, value=value):
                    result = formatter(value)
                    self.assertEqual(result, expected)
                    self.assertIs(type(result), str)
        self.assertEqual(cases, original)

    def test_negative_values_preserve_error(self) -> None:
        for formatter in (ordinal, ordinal_legacy):
            for value in (-1, -2, -11, -113, -(10**100)):
                with self.subTest(formatter=formatter.__name__, value=value):
                    with self.assertRaises(ValueError) as caught:
                        formatter(value)
                    self.assertEqual(
                        caught.exception.args, ('nonnegative value required',)
                    )

    def test_public_signatures_and_keyword_calls(self) -> None:
        expected = inspect.Signature(
            [
                inspect.Parameter(
                    'value', inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=int
                )
            ],
            return_annotation=str,
        )
        for formatter in (ordinal, ordinal_legacy):
            with self.subTest(formatter=formatter.__name__):
                self.assertEqual(inspect.signature(formatter), expected)
                self.assertEqual(formatter(value=22), '22nd')

    def test_collection_inputs_raise_without_mutation(self) -> None:
        for formatter in (ordinal, ordinal_legacy):
            for value in ([1, 2, 3], {'value': [1, 2]}, {1, 2, 3}, (1, 2, 3)):
                with self.subTest(formatter=formatter.__name__, value=value):
                    original = copy.deepcopy(value)
                    with self.assertRaises(TypeError):
                        formatter(value)
                    self.assertEqual(value, original)


if __name__ == '__main__':
    unittest.main()
