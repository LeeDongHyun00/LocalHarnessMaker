import unittest

from solution import runs


class RunsTests(unittest.TestCase):
    def test_adjacent_values_form_separate_runs(self) -> None:
        items = ["a", "a", "b", "a", "a", "a", "b", "b"]
        original = items.copy()

        self.assertEqual(runs(items), [("a", 2), ("b", 1), ("a", 3), ("b", 2)])
        self.assertEqual(items, original)

    def test_empty_input(self) -> None:
        self.assertEqual(runs([]), [])


if __name__ == "__main__":
    unittest.main()
