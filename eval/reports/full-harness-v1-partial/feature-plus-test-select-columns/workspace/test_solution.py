import unittest

from solution import select


class SelectTests(unittest.TestCase):
    def test_ordinary_rows_preserve_requested_order_and_inputs(self):
        rows = [{"a": 1, "b": 2, "c": 3}, {"a": 4, "b": 5, "c": 6}]
        columns = ["c", "a"]
        original_rows = [row.copy() for row in rows]
        original_columns = columns.copy()

        result = select(rows, columns)

        self.assertEqual(result, [{"c": 3, "a": 1}, {"c": 6, "a": 4}])
        self.assertEqual([list(row) for row in result], [["c", "a"], ["c", "a"]])
        self.assertIsNot(result, rows)
        for selected, original in zip(result, rows):
            self.assertIsNot(selected, original)
        self.assertEqual(rows, original_rows)
        self.assertEqual(columns, original_columns)
        result[0]["a"] = 99
        self.assertEqual(rows, original_rows)

    def test_missing_and_repeated_columns(self):
        rows = [{"a": 0, "b": -1}, {}, {"b": 2}]
        columns = ["b", "missing", "a", "b", "a"]

        result = select(rows, columns)

        self.assertEqual(result, [{"b": -1, "a": 0}, {}, {"b": 2}])
        self.assertEqual([list(row) for row in result], [["b", "a"], [], ["b"]])
        self.assertEqual(rows, [{"a": 0, "b": -1}, {}, {"b": 2}])
        self.assertEqual(columns, ["b", "missing", "a", "b", "a"])

    def test_empty_rows(self):
        rows = []
        for columns in ([], ["a"]):
            with self.subTest(columns=columns):
                result = select(rows, columns)
                self.assertEqual(result, [])
                self.assertIsNot(result, rows)

    def test_empty_columns_and_all_missing_keys_return_fresh_rows(self):
        rows = [{"a": 1}, {}]
        for columns in ([], ["missing"]):
            with self.subTest(columns=columns):
                result = select(rows, columns)
                self.assertEqual(result, [{}, {}])
                self.assertIsNot(result[0], result[1])
                for selected, original in zip(result, rows):
                    self.assertIsNot(selected, original)
                self.assertEqual(rows, [{"a": 1}, {}])


if __name__ == "__main__":
    unittest.main()
