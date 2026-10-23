import unittest

from solution import runs


class RunsTests(unittest.TestCase):
    def test_adjacent_runs_and_input_preservation(self) -> None:
        items = ["a", "a", "b", "b", "b", "a"]
        original = items.copy()

        self.assertEqual(runs(items), [("a", 2), ("b", 3), ("a", 1)])
        self.assertEqual(items, original)

    def test_empty_input(self) -> None:
        self.assertEqual(runs([]), [])


if __name__ == "__main__":
    unittest.main()
