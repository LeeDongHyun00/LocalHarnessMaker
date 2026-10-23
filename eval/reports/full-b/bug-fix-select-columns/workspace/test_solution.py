import unittest

from solution import select


class SelectTests(unittest.TestCase):
    def test_missing_columns_preserve_order_and_inputs(self) -> None:
        rows = [{"a": 1, "b": 2, "extra": 3}, {"b": 4}, {"a": 5}, {}]
        columns = ["b", "missing", "a", "b"]
        original_rows = [row.copy() for row in rows]
        original_columns = columns.copy()

        result = select(rows, columns)

        self.assertEqual(result, [{"b": 2, "a": 1}, {"b": 4}, {"a": 5}, {}])
        self.assertEqual([list(row) for row in result], [["b", "a"], ["b"], ["a"], []])
        self.assertEqual(rows, original_rows)
        self.assertEqual(columns, original_columns)
        self.assertIsNot(result, rows)
        for selected_row, original_row in zip(result, rows):
            self.assertIsNot(selected_row, original_row)


if __name__ == "__main__":
    unittest.main()
