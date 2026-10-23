import unittest

from solution import runs, runs_legacy


class RunsTests(unittest.TestCase):
    def test_adjacent_and_nonadjacent_values(self) -> None:
        for encode in (runs, runs_legacy):
            with self.subTest(function=encode.__name__):
                self.assertEqual(
                    encode(["a", "a", "b", "a", "a", "a", "", ""]),
                    [("a", 2), ("b", 1), ("a", 3), ("", 2)],
                )

    def test_empty_input(self) -> None:
        for encode in (runs, runs_legacy):
            with self.subTest(function=encode.__name__):
                result = encode([])
                self.assertEqual(result, [])
                self.assertIsInstance(result, list)

    def test_input_is_unchanged_and_result_is_independent(self) -> None:
        for encode in (runs, runs_legacy):
            with self.subTest(function=encode.__name__):
                items = ["a", "a", "b"]
                original = items.copy()
                result = encode(items)
                self.assertEqual(items, original)
                self.assertEqual(result, [("a", 2), ("b", 1)])
                self.assertTrue(all(isinstance(pair, tuple) for pair in result))
                result.clear()
                self.assertEqual(items, original)
                self.assertEqual(encode(items), [("a", 2), ("b", 1)])

    def test_noniterable_input_raises_type_error(self) -> None:
        for encode in (runs, runs_legacy):
            with self.subTest(function=encode.__name__):
                with self.assertRaises(TypeError):
                    encode(None)  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
