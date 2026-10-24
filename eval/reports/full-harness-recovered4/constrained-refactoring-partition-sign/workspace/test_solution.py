import unittest

from solution import partition, partition_legacy


class PartitionTests(unittest.TestCase):
    def test_order_duplicates_and_return_types(self) -> None:
        items = [3, -2, 0, -1, 3, 0, -2, 1]
        expected = ([-2, -1, -2], [0, 0], [3, 3, 1])
        for function in (partition, partition_legacy):
            with self.subTest(function=function.__name__):
                result = function(items)
                self.assertIsInstance(result, tuple)
                self.assertEqual(result, expected)
                for group in result:
                    self.assertIsInstance(group, list)

    def test_input_immutability_and_independent_outputs(self) -> None:
        for function in (partition, partition_legacy):
            with self.subTest(function=function.__name__):
                items = [-1, 0, 1]
                result = function(items)
                self.assertEqual(items, [-1, 0, 1])
                for group in result:
                    group.append(42)
                self.assertEqual(items, [-1, 0, 1])
                self.assertEqual(function(items), ([-1], [0], [1]))

    def test_empty_input_returns_distinct_lists(self) -> None:
        for function in (partition, partition_legacy):
            with self.subTest(function=function.__name__):
                result = function([])
                self.assertEqual(result, ([], [], []))
                self.assertEqual(len({id(group) for group in result}), 3)

    def test_invalid_inputs_raise_type_error_without_mutation(self) -> None:
        for function in (partition, partition_legacy):
            with self.subTest(function=function.__name__):
                items = [-1, "invalid", 1]
                with self.assertRaises(TypeError):
                    function(items)
                self.assertEqual(items, [-1, "invalid", 1])
                with self.assertRaises(TypeError):
                    function(None)


if __name__ == "__main__":
    unittest.main()
