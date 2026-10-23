import unittest

from solution import select, select_legacy


class SelectTests(unittest.TestCase):
    def test_column_order_missing_keys_duplicates_and_row_order(self):
        rows = [{"a": 1, "b": 2, "c": 3}, {"b": 4}, {"a": 5, "c": 6}]
        columns = ["c", "missing", "a", "c", "b"]
        for function in (select, select_legacy):
            with self.subTest(function=function.__name__):
                result = function(rows, columns)
                self.assertEqual(result, [{"c": 3, "a": 1, "b": 2}, {"b": 4}, {"c": 6, "a": 5}])
                self.assertEqual([list(row) for row in result], [["c", "a", "b"], ["b"], ["c", "a"]])

    def test_inputs_unchanged_and_output_dictionaries_are_new(self):
        for function in (select, select_legacy):
            with self.subTest(function=function.__name__):
                rows = [{"a": 1, "b": 2}, {"a": 3}]
                columns = ["b", "a", "b"]
                result = function(rows, columns)
                self.assertIsNot(result, rows)
                for original, selected in zip(rows, result):
                    self.assertIsNot(original, selected)
                result[0]["a"] = 99
                self.assertEqual(rows, [{"a": 1, "b": 2}, {"a": 3}])
                self.assertEqual([list(row) for row in rows], [["a", "b"], ["a"]])
                self.assertEqual(columns, ["b", "a", "b"])

    def test_empty_inputs(self):
        for function in (select, select_legacy):
            with self.subTest(function=function.__name__):
                self.assertEqual(function([], ["a"]), [])
                result = function([{}, {}], [])
                self.assertEqual(result, [{}, {}])
                self.assertIsNot(result[0], result[1])

    def test_invalid_inputs_keep_existing_type_errors(self):
        for function in (select, select_legacy):
            with self.subTest(function=function.__name__):
                with self.assertRaises(TypeError):
                    function(None, ["a"])
                with self.assertRaises(TypeError):
                    function([{"a": 1}], None)
                with self.assertRaises(TypeError):
                    function([{"a": 1}], [[]])
                self.assertEqual(function([], None), [])


if __name__ == "__main__":
    unittest.main()
