import unittest

from solution import round_robin


class RoundRobinTests(unittest.TestCase):
    def test_interleaves_groups_in_supplied_order(self) -> None:
        self.assertEqual(
            round_robin([[3, 1], [8, 6], [5, 2]]),
            [3, 8, 5, 1, 6, 2],
        )

    def test_skips_empty_and_exhausted_groups(self) -> None:
        self.assertEqual(
            round_robin([[], [1, 2, 3], [4], [], [5, 6], []]),
            [1, 4, 5, 2, 6, 3],
        )

    def test_empty_inputs(self) -> None:
        self.assertEqual(round_robin([]), [])
        self.assertEqual(round_robin([[], []]), [])

    def test_preserves_values_and_input_collections(self) -> None:
        groups = [[0, -2, 0], [7, -2], []]
        original_groups = groups.copy()
        original_values = [group.copy() for group in groups]

        result = round_robin(groups)

        self.assertEqual(result, [0, 7, -2, -2, 0])
        self.assertEqual(groups, original_values)
        for actual, original in zip(groups, original_groups):
            self.assertIs(actual, original)
            self.assertIsNot(result, actual)
        self.assertIsNot(result, groups)

    def test_shared_group_is_processed_at_each_position(self) -> None:
        shared = [9, 4]
        groups = [shared, shared]
        self.assertEqual(round_robin(groups), [9, 9, 4, 4])
        self.assertEqual(shared, [9, 4])
        self.assertIs(groups[0], groups[1])


if __name__ == "__main__":
    unittest.main()
