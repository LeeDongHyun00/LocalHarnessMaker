import unittest

from solution import interleave, interleave_legacy


class InterleaveTests(unittest.TestCase):
    def test_alternation_and_remainders(self) -> None:
        cases = [
            ([1, 2], [3, 4], [1, 3, 2, 4]),
            ([1, 2, 3], [4], [1, 4, 2, 3]),
            ([1], [2, 3, 4], [1, 2, 3, 4]),
        ]
        for function in (interleave, interleave_legacy):
            for left, right, expected in cases:
                with self.subTest(function=function.__name__, left=left, right=right):
                    result = function(left, right)
                    self.assertIs(type(result), list)
                    self.assertEqual(result, expected)

    def test_empty_inputs(self) -> None:
        for function in (interleave, interleave_legacy):
            for left, right in [([], []), ([1, 2], []), ([], [1, 2])]:
                with self.subTest(function=function.__name__, left=left, right=right):
                    result = function(left, right)
                    self.assertEqual(result, left + right)
                    self.assertIsNot(result, left)
                    self.assertIsNot(result, right)

    def test_inputs_are_unchanged(self) -> None:
        for function in (interleave, interleave_legacy):
            with self.subTest(function=function.__name__):
                left, right = [1, 2, 3], [4, 5]
                result = function(left, right)
                self.assertEqual(left, [1, 2, 3])
                self.assertEqual(right, [4, 5])
                result.append(6)
                self.assertEqual(left, [1, 2, 3])
                self.assertEqual(right, [4, 5])
                self.assertEqual(function(left, left), [1, 1, 2, 2, 3, 3])
                self.assertEqual(left, [1, 2, 3])

    def test_invalid_inputs_keep_type_errors(self) -> None:
        for function in (interleave, interleave_legacy):
            for left, right in [(None, []), ([], None), ({1}, []), ([], {1})]:
                with self.subTest(function=function.__name__, left=left, right=right):
                    with self.assertRaises(TypeError):
                        function(left, right)


if __name__ == "__main__":
    unittest.main()
