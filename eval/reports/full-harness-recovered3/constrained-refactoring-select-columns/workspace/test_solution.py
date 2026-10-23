import unittest

from solution import select, select_legacy


class SelectTests(unittest.TestCase):
    def test_column_order_missing_keys_duplicates_and_row_order(self):
        for function in (select, select_legacy):
            with self.subTest(function=function.__name__):
                rows = [{"a": 1, "b": 2, "c": 3}, {"a": 4}, {}]
                columns = ["b", "missing", "a", "b"]
                result = function(rows, columns)
                self.assertEqual(result, [{"b": 2, "a": 1}, {"a": 4}, {}])
                self.assertEqual(list(result[0]), ["b", "a"])
                self.assertEqual(rows, [{"a": 1, "b": 2, "c": 3}, {"a": 4}, {}])
                self.assertEqual(columns, ["b", "missing", "a", "b"])

    def test_results_are_fresh_and_values_are_preserved(self):
        for function in (select, select_legacy):
            with self.subTest(function=function.__name__):
                value = 12345678901234567890
                row = {"a": value}
                rows = [row, row]
                result = function(rows, ["a"])
                self.assertIsNot(result, rows)
                self.assertIsNot(result[0], row)
                self.assertIsNot(result[1], row)
                self.assertIsNot(result[0], result[1])
                self.assertIs(result[0]["a"], value)
                result[0]["a"] = 0
                self.assertEqual(row, {"a": value})
                self.assertEqual(result[1], {"a": value})

    def test_empty_inputs(self):
        for function in (select, select_legacy):
            with self.subTest(function=function.__name__):
                self.assertEqual(function([], ["a"]), [])
                result = function([{"a": 1}, {}], [])
                self.assertEqual(result, [{}, {}])
                self.assertIsNot(result[0], result[1])

    def test_error_behavior_and_lazy_empty_rows(self):
        for function in (select, select_legacy):
            with self.subTest(function=function.__name__):
                with self.assertRaises(TypeError):
                    function(None, ["a"])
                with self.assertRaises(TypeError):
                    function([{}], None)
                with self.assertRaises(TypeError):
                    function([None], ["a"])
                rows = [{"a": 1}]
                columns = [[]]
                with self.assertRaises(TypeError):
                    function(rows, columns)
                self.assertEqual(rows, [{"a": 1}])
                self.assertEqual(columns, [[]])
                self.assertEqual(function([], None), [])


if __name__ == "__main__":
    unittest.main()
