import unittest

from solution import partition, partition_legacy


class PartitionTests(unittest.TestCase):
    def test_preserves_order_and_duplicates(self) -> None:
        items = [4, -3, 0, -1, 4, 0, -3, 2]
        expected = ([-3, -1, -3], [0, 0], [4, 4, 2])
        for function in (partition, partition_legacy):
            with self.subTest(function=function.__name__):
                self.assertEqual(function(items), expected)

    def test_empty_input_returns_fresh_independent_lists(self) -> None:
        for function in (partition, partition_legacy):
            with self.subTest(function=function.__name__):
                result = function([])
                self.assertEqual(result, ([], [], []))
                result[0].append(-1)
                self.assertEqual(result, ([-1], [], []))
                self.assertEqual(function([]), ([], [], []))

    def test_input_is_unchanged_and_results_do_not_alias_it(self) -> None:
        for function in (partition, partition_legacy):
            with self.subTest(function=function.__name__):
                items = [-1, 0, 2]
                original = items.copy()
                result = function(items)
                self.assertEqual(items, original)
                for group in result:
                    group.clear()
                self.assertEqual(items, original)

    def test_non_iterable_input_raises_type_error(self) -> None:
        for function in (partition, partition_legacy):
            for items in (None, 1):
                with self.subTest(function=function.__name__, items=items):
                    with self.assertRaises(TypeError):
                        function(items)

    def test_invalid_item_raises_without_mutating_input(self) -> None:
        for function in (partition, partition_legacy):
            with self.subTest(function=function.__name__):
                items = [1, "invalid", -2]
                original = items.copy()
                with self.assertRaises(TypeError):
                    function(items)
                self.assertEqual(items, original)

    def test_zero_comparison_errors_propagate_for_negative_items(self) -> None:
        class RejectZeroComparison(int):
            def __eq__(self, other: object) -> bool:
                raise ValueError("cannot compare against zero")

        for function in (partition, partition_legacy):
            with self.subTest(function=function.__name__):
                with self.assertRaisesRegex(ValueError, "^cannot compare against zero$"):
                    function([RejectZeroComparison(-1)])


if __name__ == "__main__":
    unittest.main()
