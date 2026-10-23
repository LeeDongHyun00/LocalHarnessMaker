import unittest

from solution import last_index


class LastIndexTests(unittest.TestCase):
    def test_ordinary_inputs(self) -> None:
        self.assertEqual(last_index(["a", "b", "a", "c"], "a"), 2)
        self.assertEqual(last_index(["a", "b", "c"], "b"), 1)
        self.assertIsNone(last_index(["a", "b"], "missing"))

    def test_boundary_inputs(self) -> None:
        for items, target, expected in [
            (["a", "b"], "a", 0),
            (["a", "b"], "b", 1),
            (["a"], "a", 0),
            (["a"], "b", None),
            (["a", "a", "a"], "a", 2),
            (["", "a", ""], "", 2),
        ]:
            with self.subTest(items=items, target=target):
                self.assertEqual(last_index(items, target), expected)

    def test_empty_input(self) -> None:
        self.assertIsNone(last_index([], "a"))
        self.assertIsNone(last_index([], ""))

    def test_matching_is_case_sensitive(self) -> None:
        self.assertEqual(last_index(["a", "A", "a"], "A"), 1)
        self.assertIsNone(last_index(["a"], "A"))

    def test_input_is_not_mutated(self) -> None:
        items = ["a", "b", "a"]
        original = items.copy()
        self.assertEqual(last_index(items, "a"), 2)
        self.assertEqual(items, original)
        self.assertIsNone(last_index(items, "missing"))
        self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
