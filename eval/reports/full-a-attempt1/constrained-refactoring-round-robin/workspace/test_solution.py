import unittest

from solution import round_robin, round_robin_legacy


class RoundRobinTests(unittest.TestCase):
    def test_interleaves_uneven_groups_without_mutating_inputs(self) -> None:
        for function in (round_robin, round_robin_legacy):
            with self.subTest(function=function.__name__):
                groups = [[1, 2, 3], [], [4], [5, 6]]
                original_groups = groups.copy()
                original_values = [group.copy() for group in groups]

                result = function(groups)

                self.assertIs(type(result), list)
                self.assertEqual(result, [1, 4, 5, 2, 6, 3])
                self.assertEqual(groups, original_values)
                for group, original in zip(groups, original_groups):
                    self.assertIs(group, original)

    def test_empty_inputs(self) -> None:
        for function in (round_robin, round_robin_legacy):
            for groups in ([], [[]], [[], []]):
                with self.subTest(function=function.__name__, groups=groups):
                    self.assertEqual(function(groups), [])

    def test_invalid_inputs_preserve_type_errors_and_inputs(self) -> None:
        for function in (round_robin, round_robin_legacy):
            for groups in (None, [[1, 2], None], [[1], 3]):
                with self.subTest(function=function.__name__, groups=groups):
                    with self.assertRaises(TypeError):
                        function(groups)
                    if isinstance(groups, list):
                        self.assertEqual(groups[0], [1, 2] if groups[1] is None else [1])


if __name__ == "__main__":
    unittest.main()
