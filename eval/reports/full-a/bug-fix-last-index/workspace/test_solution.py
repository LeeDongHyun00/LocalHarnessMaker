import unittest

from solution import last_index


class LastIndexTests(unittest.TestCase):
    def test_returns_last_match_without_mutating_input(self) -> None:
        items = ["match", "other", "match", "Match"]
        original = items.copy()

        self.assertEqual(last_index(items, "match"), 2)
        self.assertEqual(items, original)

    def test_empty_absent_and_case_sensitive_matches(self) -> None:
        self.assertIsNone(last_index([], "match"))
        self.assertIsNone(last_index(["other"], "match"))
        self.assertIsNone(last_index(["Match"], "match"))
        self.assertEqual(last_index(["match"], "match"), 0)


if __name__ == "__main__":
    unittest.main()
