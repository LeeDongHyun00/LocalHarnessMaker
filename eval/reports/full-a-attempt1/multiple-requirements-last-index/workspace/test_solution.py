import unittest

from solution import last_index


class LastIndexTests(unittest.TestCase):
    def test_returns_last_matching_index(self) -> None:
        self.assertEqual(last_index(["a", "b", "a", "c", "a"], "a"), 4)
        self.assertEqual(last_index(["a", "b", "a", "c"], "a"), 2)

    def test_absent_and_empty_inputs(self) -> None:
        self.assertIsNone(last_index(["a", "b"], "c"))
        self.assertIsNone(last_index([], "a"))

    def test_matching_is_case_sensitive(self) -> None:
        self.assertEqual(last_index(["A", "a", "A"], "a"), 1)
        self.assertIsNone(last_index(["A", "A"], "a"))

    def test_preserves_input_values_and_order(self) -> None:
        for target in ("a", "missing"):
            with self.subTest(target=target):
                items = ["b", "a", "C", "a", ""]
                original = items.copy()
                last_index(items, target)
                self.assertEqual(items, original)

    def test_zero_index_and_empty_string(self) -> None:
        self.assertEqual(last_index(["a", "b"], "a"), 0)
        self.assertEqual(last_index(["", "a", ""], ""), 2)
        self.assertEqual(last_index(["a"], "a"), 0)


if __name__ == "__main__":
    unittest.main()
