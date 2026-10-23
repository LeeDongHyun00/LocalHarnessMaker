import unittest

from solution import unique, unique_legacy


class UniqueTests(unittest.TestCase):
    def test_first_occurrence_order_and_case_sensitivity(self):
        for function in (unique, unique_legacy):
            with self.subTest(function=function.__name__):
                items = ["b", "a", "b", "A", "a", "", ""]
                original = items.copy()
                result = function(items)
                self.assertIsInstance(result, list)
                self.assertEqual(result, ["b", "a", "A", ""])
                self.assertEqual(items, original)
                self.assertIsNot(result, items)

    def test_empty_input_returns_new_empty_list(self):
        for function in (unique, unique_legacy):
            with self.subTest(function=function.__name__):
                items: list[str] = []
                result = function(items)
                self.assertEqual(result, [])
                self.assertEqual(items, [])
                self.assertIsNot(result, items)

    def test_invalid_inputs_preserve_type_errors(self):
        for function in (unique, unique_legacy):
            for items in (None, [["a"]]):
                with self.subTest(function=function.__name__, items=items):
                    with self.assertRaises(TypeError) as expected:
                        list(dict.fromkeys(items))
                    with self.assertRaises(TypeError) as actual:
                        function(items)
                    self.assertEqual(str(actual.exception), str(expected.exception))
                    if items is not None:
                        self.assertEqual(items, [["a"]])


if __name__ == "__main__":
    unittest.main()
