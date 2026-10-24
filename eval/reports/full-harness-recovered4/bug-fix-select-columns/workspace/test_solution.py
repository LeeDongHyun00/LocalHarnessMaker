import unittest

from solution import select


class SelectTests(unittest.TestCase):
    def test_select_omits_missing_keys_and_preserves_inputs(self) -> None:
        rows = [{"a": 1, "b": 2, "extra": 3}, {"a": 4}, {}]
        columns = ["b", "missing", "a", "b"]
        original_rows = [row.copy() for row in rows]
        original_columns = columns.copy()

        result = select(rows, columns)

        self.assertEqual(result, [{"b": 2, "a": 1}, {"a": 4}, {}])
        self.assertEqual([list(row) for row in result], [["b", "a"], ["a"], []])
        self.assertEqual(rows, original_rows)
        self.assertEqual(columns, original_columns)
        for selected, original in zip(result, rows):
            self.assertIsNot(selected, original)


if __name__ == "__main__":
    unittest.main()
