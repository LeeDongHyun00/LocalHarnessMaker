"""Regression tests for the public round_robin API."""

import unittest

from solution import round_robin


class RoundRobinTests(unittest.TestCase):
    def test_interleaves_equal_length_groups(self) -> None:
        self.assertEqual(
            round_robin([[1, 2], [3, 4], [5, 6]]),
            [1, 3, 5, 2, 4, 6],
        )

    def test_continues_until_uneven_groups_are_exhausted(self) -> None:
        self.assertEqual(
            round_robin([[1, 2, 3], [4], [5, 6]]),
            [1, 4, 5, 2, 6, 3],
        )

    def test_handles_empty_collections_and_groups(self) -> None:
        cases: list[tuple[list[list[int]], list[int]]] = [
            ([], []),
            ([[], [], []], []),
            ([[], [1, 2], [], [3], []], [1, 3, 2]),
            ([[4, 2, 1]], [4, 2, 1]),
        ]
        for groups, expected in cases:
            with self.subTest(groups=groups):
                self.assertEqual(round_robin(groups), expected)

    def test_preserves_zero_negative_and_repeated_values(self) -> None:
        self.assertEqual(
            round_robin([[0, -3, 0], [0, 5, -3], [5]]),
            [0, 0, 5, -3, 5, 0, -3],
        )

    def test_preserves_input_values_and_collection_order(self) -> None:
        groups = [[3, 1], [], [2, 4, 0]]
        original_groups = groups.copy()
        original_values = [group.copy() for group in groups]

        result = round_robin(groups)

        self.assertEqual(result, [3, 2, 1, 4, 0])
        self.assertEqual(groups, original_values)
        for index, original_group in enumerate(original_groups):
            self.assertIs(groups[index], original_group)
        self.assertEqual(round_robin(groups), result)

        result.append(99)
        self.assertEqual(groups, original_values)

    def test_shared_groups_are_visited_independently(self) -> None:
        shared = [7, 8]
        groups = [shared, [9], shared]

        self.assertEqual(round_robin(groups), [7, 9, 7, 8, 8])
        self.assertEqual(groups, [[7, 8], [9], [7, 8]])
        self.assertIs(groups[0], shared)
        self.assertIs(groups[2], shared)


if __name__ == "__main__":
    unittest.main()
