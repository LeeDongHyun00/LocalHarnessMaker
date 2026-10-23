import unittest

from solution import select, select_legacy


class SelectTests(unittest.TestCase):
    def test_requested_columns_and_row_order(self) -> None:
        rows = [
            {"first": 1, "second": 2, "third": 3},
            {"first": 4, "third": 6},
            {"second": 8, "third": 9},
        ]
        columns = ["third", "missing", "first", "third", "second", "first"]
        expected_items = [
            [("third", 3), ("first", 1), ("second", 2)],
            [("third", 6), ("first", 4)],
            [("third", 9), ("second", 8)],
        ]

        for selector in (select, select_legacy):
            with self.subTest(selector=selector.__name__):
                result = selector(rows, columns)
                self.assertIsInstance(result, list)
                self.assertTrue(all(isinstance(row, dict) for row in result))
                self.assertEqual([list(row.items()) for row in result], expected_items)

    def test_inputs_unchanged_and_results_are_new(self) -> None:
        rows = [{"first": 1, "second": 2}, {"first": 3, "second": 4}]
        columns = ["second", "first", "second", "missing"]
        original_rows = [row.copy() for row in rows]
        original_columns = columns.copy()
        row_references = rows.copy()

        for selector in (select, select_legacy):
            with self.subTest(selector=selector.__name__):
                result = selector(rows, columns)
                self.assertIsNot(result, rows)
                self.assertIsNot(result[0], result[1])
                for actual, original in zip(result, rows):
                    self.assertIsNot(actual, original)
                    for key, value in actual.items():
                        self.assertIs(value, original[key])
                result[0]["first"] = 99
                result[1].clear()
                result.append({"extra": 5})
                self.assertEqual(rows, original_rows)
                self.assertEqual(columns, original_columns)
                for actual, original in zip(rows, row_references):
                    self.assertIs(actual, original)

    def test_empty_inputs_and_missing_columns(self) -> None:
        cases = [
            ([], ["first"], []),
            ([{"first": 1}, {"first": 2}], [], [{}, {}]),
            ([{"first": 1}, {}], ["missing"], [{}, {}]),
            ([{}], ["first"], [{}]),
        ]

        for selector in (select, select_legacy):
            for rows, columns, expected in cases:
                with self.subTest(selector=selector.__name__, rows=rows, columns=columns):
                    result = selector(rows, columns)
                    self.assertEqual(result, expected)
                    self.assertIsNot(result, rows)
                    self.assertEqual(len({id(row) for row in result}), len(result))
                    for actual, original in zip(result, rows):
                        self.assertIsNot(actual, original)

    def test_invalid_inputs_keep_type_errors(self) -> None:
        cases = [
            (None, ["first"]),
            ([None], ["first"]),
            ([{"first": 1}], None),
            ([{"first": 1}], [[]]),
        ]

        for selector in (select, select_legacy):
            for rows, columns in cases:
                with self.subTest(selector=selector.__name__, rows=rows, columns=columns):
                    with self.assertRaises(TypeError):
                        selector(rows, columns)
            with self.subTest(selector=selector.__name__, empty_rows=True):
                self.assertEqual(selector([], None), [])


if __name__ == "__main__":
    unittest.main()
