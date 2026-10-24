import unittest

from solution import last_index


class LastIndexTests(unittest.TestCase):
    def test_returns_last_matching_index(self):
        self.assertEqual(last_index(["a", "b", "a", "c", "a"], "a"), 4)
        self.assertEqual(last_index(["a", "b", "a", "c"], "a"), 2)

    def test_returns_none_for_absent_target_and_empty_input(self):
        self.assertIsNone(last_index(["a", "b"], "c"))
        self.assertIsNone(last_index([], "a"))

    def test_matching_is_case_sensitive(self):
        self.assertEqual(last_index(["A", "a", "A"], "a"), 1)
        self.assertIsNone(last_index(["A", "A"], "a"))

    def test_single_match_and_empty_string(self):
        self.assertEqual(last_index(["a"], "a"), 0)
        self.assertEqual(last_index(["", "a", ""], ""), 2)

    def test_preserves_input_values_and_order(self):
        for target in ("a", "missing"):
            with self.subTest(target=target):
                items = ["b", "a", "c", "a"]
                original = items.copy()
                last_index(items, target)
                self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
