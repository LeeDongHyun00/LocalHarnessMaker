import unittest

from solution import runs, runs_legacy


class RunsTests(unittest.TestCase):
    def test_adjacent_and_nonadjacent_runs(self):
        for encode in (runs, runs_legacy):
            with self.subTest(function=encode.__name__):
                items = ["a", "a", "b", "b", "b", "a", "", ""]
                original = items.copy()
                self.assertEqual(
                    encode(items),
                    [("a", 2), ("b", 3), ("a", 1), ("", 2)],
                )
                self.assertEqual(items, original)

    def test_empty_input(self):
        for encode in (runs, runs_legacy):
            with self.subTest(function=encode.__name__):
                items: list[str] = []
                result = encode(items)
                self.assertEqual(result, [])
                self.assertIsNot(result, items)
                self.assertEqual(items, [])

    def test_results_are_independent(self):
        for encode in (runs, runs_legacy):
            with self.subTest(function=encode.__name__):
                items = ["a"]
                result = encode(items)
                result.append(("b", 1))
                self.assertEqual(items, ["a"])
                self.assertEqual(encode(items), [("a", 1)])

    def test_noniterable_input_raises_type_error(self):
        for encode in (runs, runs_legacy):
            with self.subTest(function=encode.__name__):
                with self.assertRaises(TypeError):
                    encode(None)


if __name__ == "__main__":
    unittest.main()
