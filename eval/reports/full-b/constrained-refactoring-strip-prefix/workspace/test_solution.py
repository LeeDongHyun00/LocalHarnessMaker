import unittest

from solution import strip_prefix, strip_prefix_legacy


class StripPrefixTests(unittest.TestCase):
    def test_removes_exactly_one_matching_prefix(self) -> None:
        cases = (
            ("prefix-value", "prefix-", "value"),
            ("preprevalue", "pre", "prevalue"),
            ("ababa", "ab", "aba"),
            ("same", "same", ""),
            ("\u03c0\u03c0value", "\u03c0", "\u03c0value"),
        )
        for function in (strip_prefix, strip_prefix_legacy):
            for text, prefix, expected in cases:
                with self.subTest(function=function.__name__, text=text, prefix=prefix):
                    self.assertEqual(function(text, prefix), expected)

    def test_nonmatching_and_empty_prefix_leave_text_unchanged(self) -> None:
        cases = (
            ("value", ""),
            ("value", "missing"),
            ("aabb", "ab"),
            ("value-prefix", "prefix"),
            ("Prefix-value", "prefix-"),
            ("short", "shorter"),
            ("", "prefix"),
            ("", ""),
        )
        for function in (strip_prefix, strip_prefix_legacy):
            for text, prefix in cases:
                with self.subTest(function=function.__name__, text=text, prefix=prefix):
                    self.assertIs(function(text, prefix), text)

    def test_keyword_arguments_and_input_immutability(self) -> None:
        for function in (strip_prefix, strip_prefix_legacy):
            with self.subTest(function=function.__name__):
                inputs = ["preprevalue", "pre"]
                original = inputs.copy()
                self.assertEqual(function(text=inputs[0], prefix=inputs[1]), "prevalue")
                self.assertEqual(inputs, original)

    def test_invalid_arguments_preserve_errors_and_collections(self) -> None:
        for function in (strip_prefix, strip_prefix_legacy):
            with self.subTest(function=function.__name__):
                with self.assertRaises(TypeError):
                    function("value", 1)
                with self.assertRaises(AttributeError):
                    function(None, "pre")
                text = ["pre", "value"]
                with self.assertRaises(AttributeError):
                    function(text, "pre")
                self.assertEqual(text, ["pre", "value"])
                prefix = ["pre"]
                with self.assertRaises(TypeError):
                    function("prevalue", prefix)
                self.assertEqual(prefix, ["pre"])

    def test_falsy_prefix_preserves_short_circuit_behavior(self) -> None:
        for function in (strip_prefix, strip_prefix_legacy):
            for prefix in (None, 0, []):
                with self.subTest(function=function.__name__, prefix=prefix):
                    self.assertEqual(function("value", prefix), "value")
                    self.assertIsNone(function(None, prefix))
                    if isinstance(prefix, list):
                        self.assertEqual(prefix, [])


if __name__ == "__main__":
    unittest.main()
