import unittest

from solution import flatten


class FlattenTests(unittest.TestCase):
    def test_preserves_all_values_and_order(self):
        self.assertEqual(
            flatten([[3, 1, 3], [0, -2], [4, 5]]),
            [3, 1, 3, 0, -2, 4, 5],
        )

    def test_ignores_empty_inner_lists(self):
        self.assertEqual(flatten([[], [1, 2], [], [3], []]), [1, 2, 3])

    def test_empty_inputs_return_new_empty_lists(self):
        for items in ([], [[]], [[], []]):
            with self.subTest(items=items):
                result = flatten(items)
                self.assertEqual(result, [])
                self.assertIsNot(result, items)
                for group in items:
                    self.assertIsNot(result, group)

    def test_returns_new_list_without_mutating_input(self):
        shared = [1, 2]
        items = [shared, [], shared, [3, 4]]
        original_groups = tuple(items)
        original_values = [group.copy() for group in items]

        result = flatten(items)

        self.assertEqual(result, [1, 2, 1, 2, 3, 4])
        self.assertEqual(items, original_values)
        self.assertIsNot(result, items)
        for group, original in zip(items, original_groups):
            self.assertIs(group, original)
            self.assertIsNot(result, group)

        result.append(5)
        self.assertEqual(items, original_values)

    def test_flattens_exactly_one_level(self):
        nested = [1, 2]
        result = flatten([[nested], []])

        self.assertEqual(result, [[1, 2]])
        self.assertIs(result[0], nested)
        self.assertEqual(nested, [1, 2])


if __name__ == "__main__":
    unittest.main()
