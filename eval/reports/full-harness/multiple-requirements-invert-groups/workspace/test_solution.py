import unittest

from solution import invert


class InvertTests(unittest.TestCase):
    def test_groups_repeated_values_in_insertion_order(self):
        items = {"z": "blue", "a": "red", "m": "blue", "b": "red"}

        result = invert(items)

        self.assertEqual(result, {"blue": ["z", "m"], "red": ["a", "b"]})
        self.assertEqual(list(result), ["blue", "red"])

    def test_empty_input(self):
        self.assertEqual(invert({}), {})

    def test_preserves_exact_values_and_input_order(self):
        items = {"third": " Red ", "first": "red", "second": "", "last": " Red "}
        original = list(items.items())

        result = invert(items)

        self.assertEqual(result, {" Red ": ["third", "last"], "red": ["first"], "": ["second"]})
        self.assertEqual(list(items.items()), original)
        self.assertEqual(list(result), [" Red ", "red", ""])

    def test_result_mutation_does_not_change_input_or_later_results(self):
        items = {"a": "same", "b": "same"}
        original = list(items.items())
        result = invert(items)

        result["same"].append("extra")
        result["other"] = ["new"]

        self.assertEqual(list(items.items()), original)
        self.assertEqual(invert(items), {"same": ["a", "b"]})


if __name__ == "__main__":
    unittest.main()
