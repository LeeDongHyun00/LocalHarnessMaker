import unittest

from solution import runs, runs_legacy


class RunsTests(unittest.TestCase):
    def test_adjacent_and_nonadjacent_runs(self) -> None:
        for encode in (runs, runs_legacy):
            with self.subTest(function=encode.__name__):
                self.assertEqual(
                    encode(["a", "a", "b", "b", "b", "a", "", ""]),
                    [("a", 2), ("b", 3), ("a", 1), ("", 2)],
                )

    def test_empty_and_single_item(self) -> None:
        for encode in (runs, runs_legacy):
            with self.subTest(function=encode.__name__):
                self.assertEqual(encode([]), [])
                self.assertEqual(encode(["a"]), [("a", 1)])

    def test_input_is_unchanged_and_results_are_independent(self) -> None:
        for encode in (runs, runs_legacy):
            with self.subTest(function=encode.__name__):
                items = ["a", "a", "b"]
                original = items.copy()
                first = encode(items)
                second = encode(items)
                self.assertEqual(items, original)
                self.assertIsInstance(first, list)
                self.assertTrue(all(isinstance(pair, tuple) for pair in first))
                self.assertIsNot(first, second)
                first.clear()
                self.assertEqual(second, [("a", 2), ("b", 1)])
                self.assertEqual(items, original)

    def test_noniterable_input_raises_type_error(self) -> None:
        for encode in (runs, runs_legacy):
            with self.subTest(function=encode.__name__):
                with self.assertRaises(TypeError):
                    encode(None)  # type: ignore[arg-type]

    def test_iteration_errors_propagate(self) -> None:
        failure = RuntimeError("iteration failed")

        class BrokenList(list[str]):
            def __iter__(self):
                raise failure

        for encode in (runs, runs_legacy):
            with self.subTest(function=encode.__name__):
                with self.assertRaises(RuntimeError) as raised:
                    encode(BrokenList())
                self.assertIs(raised.exception, failure)


if __name__ == "__main__":
    unittest.main()
