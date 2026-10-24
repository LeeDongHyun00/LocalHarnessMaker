from unittest import TestCase

from solution import select


class SelectTests(TestCase):
    def test_requested_column_order_and_duplicates(self):
        rows = [{"a": 1, "b": 2, "c": 3}]

        result = select(rows, ["c", "a", "c", "b", "a"])

        self.assertEqual(result, [{"c": 3, "a": 1, "b": 2}])
        self.assertEqual(list(result[0]), ["c", "a", "b"])

    def test_missing_keys_and_row_order(self):
        rows = [{"a": 1}, {"b": 2, "a": 3}, {}, {"b": 4}]

        result = select(rows, ["b", "missing", "a"])

        self.assertEqual(result, [{"a": 1}, {"b": 2, "a": 3}, {}, {"b": 4}])
        self.assertEqual([list(row) for row in result], [["a"], ["b", "a"], [], ["b"]])

    def test_preserves_values_and_input_collections(self):
        value = 10**100
        row = {"a": value, "b": -2}
        rows = [row, row]
        columns = ["b", "a", "b", "missing"]

        result = select(rows, columns)

        self.assertIsNot(result, rows)
        self.assertIsNot(result[0], row)
        self.assertIsNot(result[1], row)
        self.assertIsNot(result[0], result[1])
        self.assertIs(result[0]["a"], value)
        self.assertEqual(rows, [{"a": value, "b": -2}] * 2)
        self.assertEqual(list(row.items()), [("a", value), ("b", -2)])
        self.assertIs(rows[0], row)
        self.assertIs(rows[1], row)
        self.assertEqual(columns, ["b", "a", "b", "missing"])
        result[0]["a"] = 0
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
