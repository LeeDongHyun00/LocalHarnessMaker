"""Regression tests for the public round_robin API."""

import unittest

from solution import round_robin


class RoundRobinTests(unittest.TestCase):
    def test_takes_one_item_per_group_each_round(self) -> None:
        self.assertEqual(
            round_robin([[1, 2, 3], [4, 5, 6], [7, 8, 9]]),
            [1, 4, 7, 2, 5, 8, 3, 6, 9],
        )

    def test_uneven_groups_and_empty_groups(self) -> None:
        self.assertEqual(
            round_robin([[], [10, 11, 12], [], [20], [30, 31], []]),
            [10, 20, 30, 11, 31, 12],
        )

    def test_empty_input(self) -> None:
        self.assertEqual(round_robin([]), [])
        self.assertEqual(round_robin([[], [], []]), [])

    def test_preserves_values_and_input_collections(self) -> None:
        groups = [[0, -2, -2], [5, 0], []]
        original_groups = groups.copy()
        original_values = [group.copy() for group in groups]

        self.assertEqual(round_robin(groups), [0, 5, -2, 0, -2])
        self.assertEqual(groups, original_values)
        for group, original in zip(groups, original_groups):
            self.assertIs(group, original)
        self.assertEqual(round_robin(groups), [0, 5, -2, 0, -2])

    def test_shared_group_is_not_modified(self) -> None:
        shared = [1, 2]
        groups = [shared, shared]
        self.assertEqual(round_robin(groups), [1, 1, 2, 2])
        self.assertEqual(shared, [1, 2])
        self.assertIs(groups[0], shared)
        self.assertIs(groups[1], shared)


if __name__ == "__main__":
    unittest.main()
