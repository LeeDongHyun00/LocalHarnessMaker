import unittest

from solution import unique, unique_legacy


class UniqueTests(unittest.TestCase):
    def test_preserves_first_occurrence_order_and_case(self) -> None:
        items = ["pear", "Apple", "pear", "apple", "Apple", "", "", "PEAR"]
        expected = ["pear", "Apple", "apple", "", "PEAR"]

        for function in (unique, unique_legacy):
            with self.subTest(function=function.__name__):
                result = function(items)
                self.assertEqual(result, expected)
                self.assertIs(type(result), list)

    def test_empty_input_returns_a_fresh_list(self) -> None:
        for function in (unique, unique_legacy):
            with self.subTest(function=function.__name__):
                items: list[str] = []
                result = function(items)
                self.assertEqual(result, [])
                self.assertIs(type(result), list)
                self.assertIsNot(result, items)

    def test_input_is_unchanged_and_result_is_independent(self) -> None:
        for function in (unique, unique_legacy):
            for items in (["b", "a", "b"], ["b", "a"]):
                with self.subTest(function=function.__name__, items=items):
                    original = items.copy()
                    result = function(items)
                    self.assertEqual(items, original)
                    self.assertIsNot(result, items)
                    result.append("new")
                    self.assertEqual(items, original)

    def test_noniterable_input_raises_type_error(self) -> None:
        for function in (unique, unique_legacy):
            for items in (None, 42):
                with self.subTest(function=function.__name__, items=items):
                    with self.assertRaises(TypeError):
                        function(items)  # type: ignore[arg-type]

    def test_unhashable_item_raises_without_mutating_input(self) -> None:
        for function in (unique, unique_legacy):
            with self.subTest(function=function.__name__):
                items = ["a", ["unhashable"], "a"]
                original = ["a", ["unhashable"], "a"]
                with self.assertRaises(TypeError):
                    function(items)  # type: ignore[arg-type]
                self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
