"""Tests for the public round_robin API."""

import unittest

from solution import round_robin


class RoundRobinTests(unittest.TestCase):
    def test_equal_length_groups(self) -> None:
        self.assertEqual(
            round_robin([[1, 2], [3, 4], [5, 6]]),
            [1, 3, 5, 2, 4, 6],
        )

    def test_uneven_groups_preserve_order_until_exhausted(self) -> None:
        self.assertEqual(
            round_robin([[1, 2, 3], [4], [5, 6, 7, 8]]),
            [1, 4, 5, 2, 6, 3, 7, 8],
        )

    def test_empty_groups_are_skipped(self) -> None:
        self.assertEqual(round_robin([[], [1, 2], [], [3], []]), [1, 3, 2])

    def test_empty_inputs(self) -> None:
        for groups in ([], [[]], [[], [], []]):
            with self.subTest(groups=groups):
                self.assertEqual(round_robin(groups), [])

    def test_single_group_and_single_item_groups(self) -> None:
        self.assertEqual(round_robin([[1, 2, 3]]), [1, 2, 3])
        self.assertEqual(round_robin([[1], [2], [3]]), [1, 2, 3])

    def test_zero_negative_values_and_duplicates(self) -> None:
        self.assertEqual(round_robin([[0, -1, 0], [2, 2], [-3]]), [0, 2, -3, -1, 2, 0])

    def test_inputs_are_not_modified(self) -> None:
        groups = [[1, 2], [], [3, 4, 5]]
        original_groups = [group.copy() for group in groups]
        group_references = groups.copy()

        self.assertEqual(round_robin(groups), [1, 3, 2, 4, 5])
        self.assertEqual(groups, original_groups)
        for current, original in zip(groups, group_references):
            self.assertIs(current, original)

    def test_shared_group_is_visited_for_each_occurrence(self) -> None:
        shared = [1, 2]
        groups = [shared, [3], shared]

        self.assertEqual(round_robin(groups), [1, 3, 1, 2, 2])
        self.assertEqual(shared, [1, 2])


if __name__ == "__main__":
    unittest.main()
