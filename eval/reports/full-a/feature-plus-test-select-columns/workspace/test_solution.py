"""Public tests for column selection."""

import unittest

from solution import select


class SelectTests(unittest.TestCase):
    def test_selects_columns_in_requested_order_and_keeps_row_order(self) -> None:
        rows = [
            {"a": 1, "b": 2, "c": 3},
            {"a": 4, "b": 5, "c": 6},
        ]

        result = select(rows, ["c", "a"])

        self.assertEqual(result, [{"c": 3, "a": 1}, {"c": 6, "a": 4}])
        self.assertEqual([list(row) for row in result], [["c", "a"], ["c", "a"]])

    def test_omits_missing_keys_and_deduplicates_columns(self) -> None:
        rows = [{"a": 0, "b": -1}, {"b": 2}, {}]

        result = select(rows, ["missing", "b", "a", "b", "a"])

        self.assertEqual(result, [{"b": -1, "a": 0}, {"b": 2}, {}])
        self.assertEqual([list(row) for row in result], [["b", "a"], ["b"], []])

    def test_empty_inputs(self) -> None:
        self.assertEqual(select([], ["a"]), [])
        self.assertEqual(select([], []), [])
        self.assertEqual(select([{"a": 1}, {}], []), [{}, {}])
        self.assertEqual(select([{}], ["a"]), [{}])

    def test_inputs_are_unchanged_and_output_rows_are_new(self) -> None:
        row = {"a": 1, "b": 2}
        rows = [row, row, {}]
        columns = ["b", "a", "b"]

        result = select(rows, columns)

        self.assertEqual(rows, [{"a": 1, "b": 2}, {"a": 1, "b": 2}, {}])
        self.assertEqual(columns, ["b", "a", "b"])
        self.assertIsNot(result, rows)
        for output_row, input_row in zip(result, rows):
            self.assertIsNot(output_row, input_row)
        self.assertIsNot(result[0], result[1])
        result[0]["a"] = 99
        self.assertEqual(row["a"], 1)
        self.assertEqual(result[1]["a"], 1)


if __name__ == "__main__":
    unittest.main()
