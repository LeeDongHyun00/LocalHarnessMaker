import unittest

from solution import round_robin, round_robin_legacy


class RoundRobinTests(unittest.TestCase):
    def test_uneven_groups_preserve_round_and_group_order(self):
        for function in (round_robin, round_robin_legacy):
            with self.subTest(function=function.__name__):
                result = function([[1, 2, 3], [], [4], [5, 6]])
                self.assertIsInstance(result, list)
                self.assertEqual(result, [1, 4, 5, 2, 6, 3])

    def test_empty_groups(self):
        for function in (round_robin, round_robin_legacy):
            for groups in ([], [[]], [[], []]):
                with self.subTest(function=function.__name__, groups=groups):
                    self.assertEqual(function(groups), [])

    def test_inputs_remain_unchanged_and_result_is_independent(self):
        for function in (round_robin, round_robin_legacy):
            with self.subTest(function=function.__name__):
                shared = [1, 2]
                groups = [shared, [], shared, [3]]
                original_groups = groups.copy()
                original_values = [group.copy() for group in groups]

                result = function(groups)

                self.assertEqual(result, [1, 1, 3, 2, 2])
                self.assertEqual(groups, original_values)
                for actual, original in zip(groups, original_groups):
                    self.assertIs(actual, original)
                result.append(99)
                self.assertEqual(groups, original_values)

    def test_invalid_inputs_raise_type_error(self):
        for function in (round_robin, round_robin_legacy):
            for groups in (None, [None], [1]):
                with self.subTest(function=function.__name__, groups=groups):
                    with self.assertRaises(TypeError):
                        function(groups)


if __name__ == "__main__":
    unittest.main()
