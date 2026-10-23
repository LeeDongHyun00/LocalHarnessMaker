import unittest

from solution import interleave, interleave_legacy


class InterleaveTests(unittest.TestCase):
    def test_alternates_left_then_right(self) -> None:
        for function in (interleave, interleave_legacy):
            with self.subTest(function=function.__name__):
                result = function([1, 2, 3], [4, 5, 6])
                self.assertIsInstance(result, list)
                self.assertEqual(result, [1, 4, 2, 5, 3, 6])

    def test_appends_remainder_in_order(self) -> None:
        cases = (
            ([1, 2, 3], [4], [1, 4, 2, 3]),
            ([1], [4, 5, 6], [1, 4, 5, 6]),
        )
        for function in (interleave, interleave_legacy):
            for left, right, expected in cases:
                with self.subTest(function=function.__name__, left=left, right=right):
                    self.assertEqual(function(left, right), expected)

    def test_empty_inputs(self) -> None:
        cases = (([], [], []), ([], [1, 2], [1, 2]), ([1, 2], [], [1, 2]))
        for function in (interleave, interleave_legacy):
            for left, right, expected in cases:
                with self.subTest(function=function.__name__, left=left, right=right):
                    result = function(left, right)
                    self.assertIsInstance(result, list)
                    self.assertEqual(result, expected)
                    self.assertIsNot(result, left)
                    self.assertIsNot(result, right)

    def test_inputs_are_unchanged_and_result_is_independent(self) -> None:
        for function in (interleave, interleave_legacy):
            with self.subTest(function=function.__name__):
                left = [1, 2]
                right = [3, 4, 5]
                result = function(left, right)
                self.assertEqual(result, [1, 3, 2, 4, 5])
                self.assertEqual(left, [1, 2])
                self.assertEqual(right, [3, 4, 5])
                result[0] = 99
                self.assertEqual(left, [1, 2])
                self.assertEqual(right, [3, 4, 5])

    def test_errors_are_preserved(self) -> None:
        for function in (interleave, interleave_legacy):
            for left, right in ((None, []), ([], None), (1, []), ([], 1)):
                with self.subTest(function=function.__name__, left=left, right=right):
                    with self.assertRaises(TypeError):
                        function(left, right)
            with self.subTest(function=function.__name__, error="missing index"):
                with self.assertRaises(KeyError) as caught:
                    function({1: 10}, [])
                self.assertEqual(caught.exception.args, (0,))


if __name__ == "__main__":
    unittest.main()
