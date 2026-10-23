import unittest
from copy import deepcopy

from solution import round_robin, round_robin_legacy


class RoundRobinTests(unittest.TestCase):
    def test_uneven_groups_preserve_round_and_group_order(self):
        for function in (round_robin, round_robin_legacy):
            with self.subTest(function=function.__name__):
                self.assertEqual(
                    function([[1, 2, 3], [], [4], [5, 6]]),
                    [1, 4, 5, 2, 6, 3],
                )

    def test_empty_groups_return_lists(self):
        for function in (round_robin, round_robin_legacy):
            for groups in ([], [[]], [[], []]):
                with self.subTest(function=function.__name__, groups=groups):
                    result = function(groups)
                    self.assertIs(type(result), list)
                    self.assertEqual(result, [])
                    self.assertIsNot(result, groups)

    def test_inputs_and_shared_groups_are_not_modified(self):
        for function in (round_robin, round_robin_legacy):
            with self.subTest(function=function.__name__):
                shared = [1, 2]
                groups = [shared, [], shared]
                original = deepcopy(groups)
                identities = [id(group) for group in groups]
                result = function(groups)
                self.assertEqual(result, [1, 1, 2, 2])
                self.assertEqual(groups, original)
                self.assertEqual([id(group) for group in groups], identities)
                result.append(99)
                self.assertEqual(groups, original)

    def test_invalid_inputs_retain_type_errors(self):
        for function in (round_robin, round_robin_legacy):
            for groups in (None, [None], [[1], 2]):
                with self.subTest(function=function.__name__, groups=groups):
                    original = deepcopy(groups)
                    with self.assertRaises(TypeError):
                        function(groups)
                    self.assertEqual(groups, original)


if __name__ == "__main__":
    unittest.main()
