"""Tests for the public select API."""

import unittest

from solution import select


class SelectTests(unittest.TestCase):
    def test_selects_columns_in_requested_order_and_preserves_rows(self) -> None:
        rows = [{"a": 1, "b": 2, "c": 3}, {"a": 4, "b": 5, "c": 6}]
        columns = ["c", "a"]

        result = select(rows, columns)

        self.assertEqual(result, [{"c": 3, "a": 1}, {"c": 6, "a": 4}])
        self.assertEqual([list(row) for row in result], [["c", "a"], ["c", "a"]])
        self.assertEqual(rows, [{"a": 1, "b": 2, "c": 3}, {"a": 4, "b": 5, "c": 6}])
        self.assertEqual(columns, ["c", "a"])
        self.assertIsNot(result, rows)
        for projected, original in zip(result, rows):
            self.assertIsNot(projected, original)
        result[0]["a"] = 99
        self.assertEqual(rows[0]["a"], 1)

    def test_missing_and_repeated_columns(self) -> None:
        rows = [{"a": 0, "b": -1}, {"b": 7}, {}]
        columns = ["missing", "b", "a", "b", "a"]

        result = select(rows, columns)

        self.assertEqual(result, [{"b": -1, "a": 0}, {"b": 7}, {}])
        self.assertEqual([list(row) for row in result], [["b", "a"], ["b"], []])
        self.assertEqual(rows, [{"a": 0, "b": -1}, {"b": 7}, {}])
        self.assertEqual(columns, ["missing", "b", "a", "b", "a"])

    def test_empty_rows(self) -> None:
        self.assertEqual(select([], ["a"]), [])
        self.assertEqual(select([], []), [])

    def test_empty_columns_return_independent_empty_dictionaries(self) -> None:
        rows = [{"a": 1}, {}]

        result = select(rows, [])

        self.assertEqual(result, [{}, {}])
        self.assertIsNot(result[0], result[1])
        for projected, original in zip(result, rows):
            self.assertIsNot(projected, original)
        self.assertEqual(rows, [{"a": 1}, {}])

    def test_all_columns_missing(self) -> None:
        self.assertEqual(select([{"a": 1}, {"b": 2}], ["x"]), [{}, {}])


if __name__ == "__main__":
    unittest.main()
