import unittest

from solution import last_index


class LastIndexTests(unittest.TestCase):
    def test_repeated_matches_return_last_index(self) -> None:
        self.assertEqual(last_index(["a", "b", "a", "c"], "a"), 2)
        self.assertEqual(last_index((1, 2, 1, 3), 1), 2)

    def test_boundary_matches(self) -> None:
        self.assertEqual(last_index(["a", "b"], "a"), 0)
        self.assertEqual(last_index(["a", "b"], "b"), 1)
        self.assertEqual(last_index(["a"], "a"), 0)
        self.assertEqual(last_index(["a", "a", "a"], "a"), 2)

    def test_empty_and_absent_inputs(self) -> None:
        self.assertIsNone(last_index([], "a"))
        self.assertIsNone(last_index((), 1))
        self.assertIsNone(last_index(["a", "b"], "c"))
        self.assertIsNone(last_index(["a"], "b"))

    def test_matching_is_case_sensitive(self) -> None:
        self.assertEqual(last_index(["a", "A", "a"], "A"), 1)
        self.assertIsNone(last_index(["a"], "A"))

    def test_input_list_is_unchanged(self) -> None:
        items = ["a", "b", "a"]
        original = items.copy()
        self.assertEqual(last_index(items, "a"), 2)
        self.assertEqual(items, original)
        self.assertIsNone(last_index(items, "c"))
        self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
