import unittest

from solution import runs


class RunsTests(unittest.TestCase):
    def test_nonadjacent_values_form_separate_runs(self) -> None:
        items = ["a", "a", "b", "b", "a"]
        original = items.copy()

        self.assertEqual(runs(items), [("a", 2), ("b", 2), ("a", 1)])
        self.assertEqual(items, original)

    def test_empty_input(self) -> None:
        self.assertEqual(runs([]), [])


if __name__ == "__main__":
    unittest.main()
