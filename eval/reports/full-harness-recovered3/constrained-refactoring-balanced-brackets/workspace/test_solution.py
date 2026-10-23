import unittest

from solution import balanced, balanced_legacy


class BalancedTests(unittest.TestCase):
    def test_bracket_nesting(self) -> None:
        cases = {
            "": True,
            "plain text": True,
            "()[]{}": True,
            "a{b[c(d)e]f}g": True,
            "([)]": False,
            "(": False,
            "[": False,
            "{": False,
            ")": False,
            "]": False,
            "}": False,
            "())": False,
            "(()": False,
        }
        for function in (balanced, balanced_legacy):
            for text, expected in cases.items():
                with self.subTest(function=function.__name__, text=text):
                    self.assertIs(function(text), expected)

    def test_input_collections_are_unchanged(self) -> None:
        for function in (balanced, balanced_legacy):
            for text, expected in (("{a[]}", True), ("([)]", False)):
                for collection in (list(text), tuple(text)):
                    with self.subTest(function=function.__name__, collection=collection):
                        original = collection[:]
                        self.assertIs(function(collection), expected)
                        self.assertEqual(collection, original)

    def test_invalid_inputs_keep_type_errors(self) -> None:
        for function in (balanced, balanced_legacy):
            for value in (None, 42, [1], [None]):
                with self.subTest(function=function.__name__, value=value):
                    with self.assertRaises(TypeError):
                        function(value)


if __name__ == "__main__":
    unittest.main()
