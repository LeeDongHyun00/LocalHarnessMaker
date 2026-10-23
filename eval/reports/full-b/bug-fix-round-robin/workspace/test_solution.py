import unittest

from solution import round_robin


class RoundRobinTests(unittest.TestCase):
    def test_uneven_groups_preserve_order_and_inputs(self) -> None:
        groups = [[1, 2, 3], [], [4], [5, 6]]
        original = [group.copy() for group in groups]

        self.assertEqual(round_robin(groups), [1, 4, 5, 2, 6, 3])
        self.assertEqual(groups, original)

    def test_empty_groups(self) -> None:
        self.assertEqual(round_robin([]), [])
        self.assertEqual(round_robin([[], []]), [])


if __name__ == "__main__":
    unittest.main()
