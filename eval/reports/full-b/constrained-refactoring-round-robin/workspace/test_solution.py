import unittest
from copy import deepcopy

from solution import round_robin, round_robin_legacy


class RoundRobinTests(unittest.TestCase):
    def test_interleaves_uneven_groups_in_order(self) -> None:
        groups = [[3, 3, -1], [2], [], [0, 0, 0, 4]]
        for function in (round_robin, round_robin_legacy):
            with self.subTest(function=function.__name__):
                self.assertEqual(function(groups), [3, 2, 0, 3, 0, -1, 0, 4])

    def test_empty_and_single_groups(self) -> None:
        cases = [([], []), ([[], []], []), ([[], [2, 1], []], [2, 1])]
        for function in (round_robin, round_robin_legacy):
            for groups, expected in cases:
                with self.subTest(function=function.__name__, groups=groups):
                    self.assertEqual(function(groups), expected)

    def test_preserves_inputs_including_shared_groups(self) -> None:
        for function in (round_robin, round_robin_legacy):
            with self.subTest(function=function.__name__):
                shared = [1, 2, 3]
                groups = [shared, [], [4], shared]
                original_groups = groups.copy()
                original_values = deepcopy(groups)

                result = function(groups)

                self.assertEqual(result, [1, 4, 1, 2, 2, 3, 3])
                self.assertEqual(groups, original_values)
                for group, original in zip(groups, original_groups):
                    self.assertIs(group, original)
                result.append(99)
                self.assertEqual(groups, original_values)

    def test_accepts_keyword_argument_and_returns_fresh_list(self) -> None:
        for function in (round_robin, round_robin_legacy):
            with self.subTest(function=function.__name__):
                groups = [[1, 2], [3]]
                result = function(groups=groups)
                self.assertIs(type(result), list)
                self.assertEqual(result, [1, 3, 2])
                self.assertIsNot(result, function(groups=groups))

    def test_invalid_inputs_raise_type_error(self) -> None:
        for function in (round_robin, round_robin_legacy):
            for groups in (None, 1, [None], [[1], 2]):
                with self.subTest(function=function.__name__, groups=groups):
                    with self.assertRaises(TypeError):
                        function(groups)


if __name__ == "__main__":
    unittest.main()
