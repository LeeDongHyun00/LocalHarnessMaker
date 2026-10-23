import unittest

from solution import runs, runs_legacy


class RunsTests(unittest.TestCase):
    def test_run_length_encoding(self) -> None:
        cases = [
            ([], []),
            (["a"], [("a", 1)]),
            (["a", "a", "a"], [("a", 3)]),
            (["a", "b", "a"], [("a", 1), ("b", 1), ("a", 1)]),
            (
                ["a", "a", "b", "b", "b", "a"],
                [("a", 2), ("b", 3), ("a", 1)],
            ),
            (["", "", "x", ""], [("", 2), ("x", 1), ("", 1)]),
        ]
        for encode in (runs, runs_legacy):
            for items, expected in cases:
                with self.subTest(function=encode.__name__, items=items):
                    result = encode(items)
                    self.assertIsInstance(result, list)
                    self.assertEqual(result, expected)
                    self.assertTrue(all(isinstance(pair, tuple) for pair in result))

    def test_input_is_unchanged(self) -> None:
        for encode in (runs, runs_legacy):
            with self.subTest(function=encode.__name__):
                items = ["a", "a", "b", "a"]
                original = items.copy()
                result = encode(items)
                self.assertEqual(items, original)
                result.clear()
                self.assertEqual(items, original)

    def test_results_are_independent(self) -> None:
        for items in ([], ["a", "a"]):
            for encode in (runs, runs_legacy):
                with self.subTest(function=encode.__name__, items=items):
                    first = encode(items)
                    second = encode(items)
                    expected = second.copy()
                    self.assertIsNot(first, second)
                    first.append(("extra", 1))
                    self.assertEqual(second, expected)

    def test_noniterable_inputs_raise_type_error(self) -> None:
        for encode in (runs, runs_legacy):
            for items in (None, 42):
                with self.subTest(function=encode.__name__, items=items):
                    with self.assertRaises(TypeError):
                        encode(items)  # type: ignore[arg-type]

    def test_comparison_errors_propagate_without_mutating_input(self) -> None:
        error = ValueError("comparison failed")

        class ExplodingString(str):
            def __eq__(self, other: object) -> bool:
                raise error

        for encode in (runs, runs_legacy):
            with self.subTest(function=encode.__name__):
                first = ExplodingString("a")
                items = [first, "a"]
                with self.assertRaises(ValueError) as raised:
                    encode(items)
                self.assertIs(raised.exception, error)
                self.assertEqual(len(items), 2)
                self.assertIs(items[0], first)
                self.assertEqual(items[1], "a")


if __name__ == "__main__":
    unittest.main()
