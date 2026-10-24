import unittest

from solution import unique


class UniqueTests(unittest.TestCase):
    def test_preserves_first_occurrence_order(self):
        self.assertEqual(
            unique(["pear", "apple", "pear", "banana", "apple"]),
            ["pear", "apple", "banana"],
        )

    def test_empty_input(self):
        self.assertEqual(unique([]), [])

    def test_case_sensitive_equality(self):
        self.assertEqual(unique(["A", "a", "A", "a"]), ["A", "a"])

    def test_preserves_string_values(self):
        self.assertEqual(
            unique(["", " apple ", "apple", "é", "e\u0301", "", " apple "]),
            ["", " apple ", "apple", "é", "e\u0301"],
        )

    def test_does_not_mutate_input(self):
        items = ["z", "a", "z", "b"]
        original = items.copy()
        result = unique(items)
        self.assertEqual(items, original)
        self.assertEqual(result, ["z", "a", "b"])
        self.assertIsNot(result, items)
        result.append("new")
        self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
