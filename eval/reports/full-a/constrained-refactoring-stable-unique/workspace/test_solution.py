import unittest

from solution import unique, unique_legacy


class UniqueTests(unittest.TestCase):
    def test_first_occurrence_order_and_case_sensitivity(self) -> None:
        for function in (unique, unique_legacy):
            with self.subTest(function=function.__name__):
                self.assertEqual(
                    function(["b", "a", "b", "A", "a", "", ""]),
                    ["b", "a", "A", ""],
                )

    def test_empty_input_returns_new_list(self) -> None:
        for function in (unique, unique_legacy):
            with self.subTest(function=function.__name__):
                items: list[str] = []
                result = function(items)
                self.assertEqual(result, [])
                self.assertIs(type(result), list)
                self.assertIsNot(result, items)

    def test_input_is_unchanged_and_result_is_independent(self) -> None:
        for function in (unique, unique_legacy):
            with self.subTest(function=function.__name__):
                items = ["b", "a", "b"]
                result = function(items)
                self.assertIs(type(result), list)
                self.assertEqual(items, ["b", "a", "b"])
                result.append("c")
                self.assertEqual(items, ["b", "a", "b"])

    def test_invalid_inputs_preserve_type_errors(self) -> None:
        for function in (unique, unique_legacy):
            for items in (None, [["a"]]):
                with self.subTest(function=function.__name__, items=items):
                    with self.assertRaises(TypeError):
                        function(items)  # type: ignore[arg-type]
                    self.assertEqual(items, None if items is None else [["a"]])


if __name__ == "__main__":
    unittest.main()
