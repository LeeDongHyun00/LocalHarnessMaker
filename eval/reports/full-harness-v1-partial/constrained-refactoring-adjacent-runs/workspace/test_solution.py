import unittest

from solution import runs, runs_legacy


class RunsTests(unittest.TestCase):
    def test_adjacent_runs_and_input_immutability(self):
        for encode in (runs, runs_legacy):
            with self.subTest(function=encode.__name__):
                items = ["a", "a", "b", "a", "a", "a", "", ""]
                original = items.copy()
                result = encode(items)
                self.assertEqual(result, [("a", 2), ("b", 1), ("a", 3), ("", 2)])
                self.assertIsInstance(result, list)
                self.assertTrue(all(isinstance(pair, tuple) for pair in result))
                self.assertEqual(items, original)

    def test_empty_and_single_item(self):
        for encode in (runs, runs_legacy):
            for items, expected in (([], []), (["a"], [("a", 1)])):
                with self.subTest(function=encode.__name__, items=items):
                    self.assertEqual(encode(items), expected)

    def test_non_iterable_raises_type_error(self):
        for encode in (runs, runs_legacy):
            with self.subTest(function=encode.__name__):
                with self.assertRaises(TypeError):
                    encode(None)


if __name__ == "__main__":
    unittest.main()
