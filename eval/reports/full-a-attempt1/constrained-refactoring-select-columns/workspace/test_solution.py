import unittest

from solution import select, select_legacy


class SelectTests(unittest.TestCase):
    def test_requested_order_missing_keys_and_repeated_columns(self):
        rows = [{"a": 1, "b": 2, "c": 3}, {"c": 4, "a": 5}, {}]
        columns = ["b", "missing", "a", "b", "c"]
        for function in (select, select_legacy):
            with self.subTest(function=function.__name__):
                result = function(rows, columns)
                self.assertEqual(result, [{"b": 2, "a": 1, "c": 3},
                                          {"a": 5, "c": 4}, {}])
                self.assertEqual([list(row) for row in result],
                                 [["b", "a", "c"], ["a", "c"], []])

    def test_new_dictionaries_and_unchanged_inputs(self):
        rows = [{"a": 1, "b": 2}, {"a": 3}]
        columns = ["b", "a", "b"]
        for function in (select, select_legacy):
            with self.subTest(function=function.__name__):
                result = function(rows, columns)
                self.assertIsNot(result, rows)
                for original, selected in zip(rows, result):
                    self.assertIsNot(selected, original)
                    for key, value in selected.items():
                        self.assertIs(value, original[key])
                result[0]["a"] = 99
                self.assertEqual(rows, [{"a": 1, "b": 2}, {"a": 3}])
                self.assertEqual([list(row) for row in rows], [["a", "b"], ["a"]])
                self.assertEqual(columns, ["b", "a", "b"])

    def test_empty_inputs(self):
        for function in (select, select_legacy):
            with self.subTest(function=function.__name__):
                self.assertEqual(function([], ["a"]), [])
                result = function([{"a": 1}, {}], [])
                self.assertEqual(result, [{}, {}])
                self.assertIsNot(result[0], result[1])

    def test_error_behavior_and_lazy_column_access(self):
        for function in (select, select_legacy):
            with self.subTest(function=function.__name__):
                with self.assertRaises(TypeError):
                    function(None, ["a"])
                with self.assertRaises(TypeError):
                    function([{}], None)
                with self.assertRaises(TypeError):
                    function([{}], [[]])
                self.assertEqual(function([], None), [])


if __name__ == "__main__":
    unittest.main()
