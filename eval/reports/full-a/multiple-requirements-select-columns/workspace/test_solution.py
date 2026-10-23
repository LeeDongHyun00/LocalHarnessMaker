import unittest

from solution import select


class SelectTests(unittest.TestCase):
    def test_requested_column_order_and_duplicates(self):
        rows = [{"a": 1, "b": 2, "c": 3}]

        result = select(rows, ["c", "a", "c", "b", "a"])

        self.assertEqual(result, [{"c": 3, "a": 1, "b": 2}])
        self.assertEqual(list(result[0]), ["c", "a", "b"])

    def test_missing_keys_are_omitted_and_row_order_is_preserved(self):
        rows = [{"a": 1}, {"b": 2, "a": 3}, {}, {"b": 4}]

        result = select(rows, ["missing", "b", "a"])

        self.assertEqual(result, [{"a": 1}, {"b": 2, "a": 3}, {}, {"b": 4}])
        self.assertEqual(list(result[1]), ["b", "a"])

    def test_inputs_and_values_are_preserved_and_results_are_new(self):
        value = 10**100
        row = {"b": 0, "a": value, "c": -7}
        rows = [row, row]
        columns = ["a", "missing", "b", "a"]
        original_items = list(row.items())
        original_columns = columns.copy()

        result = select(rows, columns)

        self.assertEqual(list(row.items()), original_items)
        self.assertEqual(columns, original_columns)
        self.assertEqual(len(rows), 2)
        self.assertIs(rows[0], row)
        self.assertIs(rows[1], row)
        self.assertIs(result[0]["a"], value)
        self.assertEqual(result, [{"a": value, "b": 0}, {"a": value, "b": 0}])
        self.assertIsNot(result, rows)
        self.assertIsNot(result[0], row)
        self.assertIsNot(result[1], row)
        self.assertIsNot(result[0], result[1])
        result[0]["a"] = 5
        self.assertEqual(row["a"], value)
        self.assertEqual(result[1]["a"], value)

    def test_empty_inputs(self):
        self.assertEqual(select([], ["a"]), [])
        rows = [{"a": 1}, {}]
        result = select(rows, [])
        self.assertEqual(result, [{}, {}])
        self.assertIsNot(result[0], rows[0])
        self.assertIsNot(result[1], rows[1])
        self.assertIsNot(result[0], result[1])


if __name__ == "__main__":
    unittest.main()
