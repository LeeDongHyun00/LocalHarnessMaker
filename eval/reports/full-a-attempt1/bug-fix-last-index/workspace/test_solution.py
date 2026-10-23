import unittest

from solution import last_index


class LastIndexTests(unittest.TestCase):
    def test_last_match_without_mutating_input(self) -> None:
        items = ["apple", "pear", "apple", "Apple"]
        self.assertEqual(last_index(items, "apple"), 2)
        self.assertEqual(items, ["apple", "pear", "apple", "Apple"])

    def test_empty_absent_and_case_sensitive_matches(self) -> None:
        self.assertIsNone(last_index([], "apple"))
        self.assertIsNone(last_index(["pear"], "apple"))
        self.assertIsNone(last_index(["Apple"], "apple"))
        self.assertEqual(last_index(["apple"], "apple"), 0)


if __name__ == "__main__":
    unittest.main()
