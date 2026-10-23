import unittest

from solution import partition, partition_legacy


class PartitionTests(unittest.TestCase):
    def test_order_duplicates_and_input_immutability(self):
        for function in (partition, partition_legacy):
            with self.subTest(function=function.__name__):
                items = [3, -2, 0, -1, 3, 0, -2, 1]
                original = items.copy()
                result = function(items)
                self.assertIsInstance(result, tuple)
                self.assertEqual(result, ([-2, -1, -2], [0, 0], [3, 3, 1]))
                self.assertTrue(all(isinstance(group, list) for group in result))
                self.assertEqual(items, original)
                result[0].append(-99)
                self.assertEqual(items, original)

    def test_empty_input_returns_independent_lists(self):
        for function in (partition, partition_legacy):
            with self.subTest(function=function.__name__):
                result = function([])
                self.assertEqual(result, ([], [], []))
                result[0].append(-1)
                self.assertEqual(result, ([-1], [], []))
                self.assertEqual(function([]), ([], [], []))

    def test_invalid_element_raises_without_mutating_input(self):
        for function in (partition, partition_legacy):
            with self.subTest(function=function.__name__):
                items = [-1, "invalid", 0, 1]
                original = items.copy()
                with self.assertRaises(TypeError):
                    function(items)
                self.assertEqual(items, original)

    def test_non_iterable_raises_type_error(self):
        for function in (partition, partition_legacy):
            with self.subTest(function=function.__name__):
                with self.assertRaises(TypeError):
                    function(None)


if __name__ == "__main__":
    unittest.main()
