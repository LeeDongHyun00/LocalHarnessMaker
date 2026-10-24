"""Tests for the public round_robin API."""

import unittest

from solution import round_robin


class RoundRobinTests(unittest.TestCase):
    def test_equal_length_groups(self) -> None:
        self.assertEqual(
            round_robin([[1, 2], [3, 4], [5, 6]]),
            [1, 3, 5, 2, 4, 6],
        )

    def test_unequal_lengths_and_empty_groups(self) -> None:
        self.assertEqual(
            round_robin([[], [1, 2, 3], [4], [], [5, 6], []]),
            [1, 4, 5, 2, 6, 3],
        )

    def test_empty_inputs(self) -> None:
        self.assertEqual(round_robin([]), [])
        self.assertEqual(round_robin([[], [], []]), [])

    def test_single_group_and_singleton_groups(self) -> None:
        self.assertEqual(round_robin([[0, -1, 0]]), [0, -1, 0])
        self.assertEqual(round_robin([[1], [2], [3]]), [1, 2, 3])

    def test_inputs_are_preserved_and_result_is_independent(self) -> None:
        shared = [1, 2]
        groups = [shared, [], shared, [3]]
        original_groups = groups.copy()
        original_contents = [group.copy() for group in groups]

        result = round_robin(groups)

        self.assertEqual(result, [1, 1, 3, 2, 2])
        self.assertEqual(groups, original_contents)
        for group, original in zip(groups, original_groups):
            self.assertIs(group, original)
        result.append(99)
        self.assertEqual(groups, original_contents)


if __name__ == "__main__":
    unittest.main()
