import unittest

from solution import last_index, last_index_legacy


class LastIndexTests(unittest.TestCase):
    def test_last_match_and_input_immutability(self) -> None:
        for function in (last_index, last_index_legacy):
            with self.subTest(function=function.__name__):
                items = ["apple", "pear", "apple", "orange"]
                original = items.copy()
                self.assertEqual(function(items, "apple"), 2)
                self.assertEqual(function(items, "pear"), 1)
                self.assertEqual(function(items, "orange"), 3)
                self.assertEqual(function(["apple"], "apple"), 0)
                self.assertEqual(items, original)

    def test_absent_empty_and_case_sensitive_matches(self) -> None:
        for function in (last_index, last_index_legacy):
            with self.subTest(function=function.__name__):
                self.assertIsNone(function([], "apple"))
                self.assertIsNone(function(["pear"], "apple"))
                self.assertIsNone(function(["Apple"], "apple"))
                self.assertEqual(function(["apple", "Apple"], "apple"), 0)

    def test_invalid_input_preserves_type_error(self) -> None:
        for function in (last_index, last_index_legacy):
            with self.subTest(function=function.__name__):
                with self.assertRaises(TypeError):
                    function(None, "apple")
                with self.assertRaises(TypeError):
                    function(iter(["apple"]), "apple")


if __name__ == "__main__":
    unittest.main()
