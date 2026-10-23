"""Tests for the public select API."""

import unittest

from solution import select


class SelectTests(unittest.TestCase):
    def test_requested_column_order_and_row_order(self) -> None:
        rows = [
            {"extra": 99, "age": 31, "id": 2},
            {"age": 0, "id": 1, "extra": -1},
        ]

        result = select(rows, ["id", "age"])

        self.assertEqual(result, [{"id": 2, "age": 31}, {"id": 1, "age": 0}])
        for row in result:
            self.assertEqual(list(row), ["id", "age"])

    def test_missing_keys_and_empty_rows(self) -> None:
        rows = [{"a": 1}, {}, {"b": 2, "a": 3}, {"unrequested": 4}]

        result = select(rows, ["missing", "b", "a"])

        self.assertEqual(result, [{"a": 1}, {}, {"b": 2, "a": 3}, {}])
        self.assertEqual([list(row) for row in result], [["a"], [], ["b", "a"], []])

    def test_repeated_columns_appear_once_in_first_requested_order(self) -> None:
        result = select(
            [{"a": 1, "b": 2, "c": 3}],
            ["b", "a", "b", "missing", "c", "a", "missing"],
        )

        self.assertEqual(result, [{"b": 2, "a": 1, "c": 3}])
        self.assertEqual(list(result[0]), ["b", "a", "c"])

    def test_empty_input_rows(self) -> None:
        for columns in ([], ["a"], ["a", "a"]):
            with self.subTest(columns=columns):
                rows: list[dict[str, int]] = []

                result = select(rows, columns)

                self.assertEqual(result, [])
                self.assertIsNot(result, rows)

    def test_empty_columns_return_a_new_empty_dictionary_for_each_row(self) -> None:
        rows = [{"a": 1}, {}, {"b": 2}]

        result = select(rows, [])

        self.assertEqual(result, [{}, {}, {}])
        self.assertEqual(len({id(row) for row in result}), len(rows))
        for source, projected in zip(rows, result):
            self.assertIsNot(projected, source)
        self.assertEqual(rows, [{"a": 1}, {}, {"b": 2}])

    def test_values_are_preserved(self) -> None:
        row = {"negative": -7, "zero": 0, "large": 10**100}

        result = select([row], ["large", "zero", "negative"])

        self.assertEqual(result, [{"large": 10**100, "zero": 0, "negative": -7}])
        for column in row:
            self.assertIs(result[0][column], row[column])

    def test_inputs_are_unchanged_and_result_rows_are_independent(self) -> None:
        source = {"a": 1, "b": 2}
        rows = [source, source]
        columns = ["b", "missing", "b", "a"]

        result = select(rows, columns)

        self.assertIsNot(result, rows)
        self.assertEqual(rows, [{"a": 1, "b": 2}, {"a": 1, "b": 2}])
        self.assertEqual(list(source), ["a", "b"])
        self.assertEqual(columns, ["b", "missing", "b", "a"])
        for index, row in enumerate(rows):
            self.assertIs(row, source)
            self.assertIsNot(result[index], source)
        self.assertIsNot(result[0], result[1])

        result[0]["a"] = 99
        result[0]["new"] = 100
        self.assertEqual(source, {"a": 1, "b": 2})
        self.assertEqual(result[1], {"b": 2, "a": 1})


if __name__ == "__main__":
    unittest.main()
