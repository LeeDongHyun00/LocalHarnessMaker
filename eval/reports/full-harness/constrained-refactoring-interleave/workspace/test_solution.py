import unittest

from solution import interleave, interleave_legacy


class InterleaveTests(unittest.TestCase):
    def test_alternation_and_remainders(self) -> None:
        cases = [
            ([1, 2], [3, 4], [1, 3, 2, 4]),
            ([1, 2, 3, 4], [5], [1, 5, 2, 3, 4]),
            ([1], [2, 3, 4, 5], [1, 2, 3, 4, 5]),
            ([], [], []),
            ([1, 2], [], [1, 2]),
            ([], [3, 4], [3, 4]),
        ]
        for function in (interleave, interleave_legacy):
            for left, right, expected in cases:
                with self.subTest(function=function.__name__, left=left, right=right):
                    result = function(left=left, right=right)
                    self.assertIs(type(result), list)
                    self.assertEqual(result, expected)

    def test_inputs_unchanged_and_result_independent(self) -> None:
        for function in (interleave, interleave_legacy):
            for left, right in (([1, 2], [3]), ([], [4]), ([5], []), ([], [])):
                with self.subTest(function=function.__name__, left=left, right=right):
                    original_left, original_right = left.copy(), right.copy()
                    result = function(left, right)
                    self.assertIsNot(result, left)
                    self.assertIsNot(result, right)
                    result.append(99)
                    self.assertEqual(left, original_left)
                    self.assertEqual(right, original_right)
            shared = [1, 2]
            self.assertEqual(function(shared, shared), [1, 1, 2, 2])
            self.assertEqual(shared, [1, 2])

    def test_unsupported_inputs_raise_type_error(self) -> None:
        for function in (interleave, interleave_legacy):
            for invalid in (None, 42, iter([1, 2]), {1, 2}):
                for args in ((invalid, []), ([], invalid)):
                    with self.subTest(function=function.__name__, args=args):
                        with self.assertRaises(TypeError):
                            function(*args)


if __name__ == "__main__":
    unittest.main()
