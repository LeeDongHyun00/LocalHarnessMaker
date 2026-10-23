import unittest

from solution import select


class SelectTests(unittest.TestCase):
    def test_preserves_row_order_and_requested_column_order(self) -> None:
        rows = [
            {"id": 2, "first": 20, "second": 21},
            {"id": 1, "first": 10, "second": 11},
        ]

        result = select(rows, ["second", "id", "first"])

        self.assertEqual(
            [list(row.items()) for row in result],
            [
                [("second", 21), ("id", 2), ("first", 20)],
                [("second", 11), ("id", 1), ("first", 10)],
            ],
        )

    def test_omits_missing_keys_and_keeps_every_row(self) -> None:
        rows = [{"a": 1}, {"b": 2}, {}, {"unrequested": 3}]

        result = select(rows, ["missing", "b", "a"])

        self.assertEqual(result, [{"a": 1}, {"b": 2}, {}, {}])

    def test_repeated_columns_keep_first_occurrence_order(self) -> None:
        rows = [{"a": 1, "b": 2, "c": 3}]

        result = select(rows, ["b", "a", "b", "missing", "c", "a"])

        self.assertEqual(list(result[0].items()), [("b", 2), ("a", 1), ("c", 3)])

    def test_preserves_values(self) -> None:
        values = {"zero": 0, "negative": -7, "large": 10**100}

        result = select([values], ["large", "zero", "negative"])

        self.assertEqual(result, [values])
        for key, value in values.items():
            with self.subTest(key=key):
                self.assertIs(result[0][key], value)

    def test_leaves_input_collections_and_rows_unchanged(self) -> None:
        rows = [{"b": 2, "a": 1}, {"c": 3, "a": 4}]
        columns = ["a", "missing", "b", "a"]
        original_rows = rows.copy()
        original_items = [list(row.items()) for row in rows]
        original_columns = columns.copy()

        result = select(rows, columns)

        self.assertIsNot(result, rows)
        self.assertEqual([list(row.items()) for row in rows], original_items)
        self.assertEqual(columns, original_columns)
        for row, original, selected in zip(rows, original_rows, result, strict=True):
            self.assertIs(row, original)
            self.assertIsNot(selected, row)

    def test_repeated_input_rows_get_independent_new_dictionaries(self) -> None:
        row = {"a": 1, "b": 2}
        rows = [row, row]

        result = select(rows, ["a"])

        self.assertEqual(result, [{"a": 1}, {"a": 1}])
        self.assertIsNot(result[0], row)
        self.assertIsNot(result[1], row)
        self.assertIsNot(result[0], result[1])
        result[0]["a"] = 99
        self.assertEqual(result[1], {"a": 1})
        self.assertEqual(rows, [{"a": 1, "b": 2}, {"a": 1, "b": 2}])

    def test_empty_rows(self) -> None:
        rows: list[dict[str, int]] = []

        result = select(rows, ["a", "a"])

        self.assertEqual(result, [])
        self.assertIsNot(result, rows)

    def test_empty_columns_return_distinct_empty_dictionaries(self) -> None:
        rows = [{"a": 1}, {"b": 2}, {}]

        result = select(rows, [])

        self.assertEqual(result, [{}, {}, {}])
        self.assertEqual(len({id(row) for row in result}), len(rows))
        for row, selected in zip(rows, result, strict=True):
            self.assertIsNot(selected, row)


if __name__ == "__main__":
    unittest.main()
