import unittest

from solution import select


class SelectTests(unittest.TestCase):
    def test_requested_columns_and_row_order(self) -> None:
        rows = [{"a": 1, "b": 2, "c": 3}, {"a": 4, "b": 5, "c": 6}]

        result = select(rows, ["c", "a"])

        self.assertEqual(result, [{"c": 3, "a": 1}, {"c": 6, "a": 4}])
        self.assertEqual([list(row) for row in result], [["c", "a"], ["c", "a"]])

    def test_duplicates_missing_keys_and_empty_rows(self) -> None:
        rows = [{"a": 0, "b": -7}, {}, {"b": 9}]

        result = select(rows, ["missing", "b", "a", "b"])

        self.assertEqual(result, [{"b": -7, "a": 0}, {}, {"b": 9}])
        self.assertEqual([list(row) for row in result], [["b", "a"], [], ["b"]])

    def test_empty_inputs(self) -> None:
        self.assertEqual(select([], ["a"]), [])
        self.assertEqual(select([], []), [])
        rows = [{"a": 1}, {}]
        result = select(rows, [])
        self.assertEqual(result, [{}, {}])
        self.assertIsNot(result[0], result[1])
        for original, selected in zip(rows, result):
            self.assertIsNot(original, selected)

    def test_inputs_unchanged_and_output_rows_are_new(self) -> None:
        rows = [{"a": 1, "b": 2}, {"a": 3}]
        columns = ["b", "a", "b"]
        original_items = [list(row.items()) for row in rows]
        original_columns = columns.copy()

        result = select(rows, columns)

        self.assertIsNot(result, rows)
        self.assertEqual([list(row.items()) for row in rows], original_items)
        self.assertEqual(columns, original_columns)
        for original, selected in zip(rows, result):
            self.assertIsNot(original, selected)
        result[0]["a"] = 100
        self.assertEqual(rows[0]["a"], 1)


if __name__ == "__main__":
    unittest.main()
