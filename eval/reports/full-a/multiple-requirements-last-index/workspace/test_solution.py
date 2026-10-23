"""Regression tests for the public last_index API."""

import unittest

from solution import last_index


class LastIndexTests(unittest.TestCase):
    def test_returns_last_matching_index(self) -> None:
        self.assertEqual(last_index(["a", "b", "a", "c", "a"], "a"), 4)
        self.assertEqual(last_index(["a", "b", "a", "c"], "a"), 2)

    def test_absent_and_empty_inputs(self) -> None:
        self.assertIsNone(last_index(["a", "b"], "missing"))
        self.assertIsNone(last_index([], "a"))

    def test_matching_is_case_sensitive(self) -> None:
        self.assertEqual(last_index(["a", "A", "a"], "A"), 1)
        self.assertIsNone(last_index(["a", "a"], "A"))

    def test_first_index_and_single_item(self) -> None:
        self.assertEqual(last_index(["a", "b"], "a"), 0)
        self.assertEqual(last_index([""], ""), 0)

    def test_preserves_input_values_and_order(self) -> None:
        items = ["z", "a", "z", "B", ""]
        original = items.copy()
        for target, expected in (("z", 2), ("missing", None), ("", 4)):
            with self.subTest(target=target):
                self.assertEqual(last_index(items, target), expected)
                self.assertEqual(items, original)
                self.assertTrue(all(a is b for a, b in zip(items, original)))


if __name__ == "__main__":
    unittest.main()
