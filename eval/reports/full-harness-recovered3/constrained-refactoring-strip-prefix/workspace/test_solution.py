import unittest

from solution import strip_prefix, strip_prefix_legacy


class StripPrefixTests(unittest.TestCase):
    def test_removes_exactly_one_whole_prefix(self) -> None:
        for function in (strip_prefix, strip_prefix_legacy):
            for text, prefix, expected in (
                ("prefix-value", "prefix-", "value"),
                ("ababvalue", "ab", "abvalue"),
                ("abba", "ab", "ba"),
                ("same", "same", ""),
                ("你好世界", "你好", "世界"),
            ):
                with self.subTest(function=function.__name__, text=text):
                    self.assertEqual(function(text, prefix), expected)

    def test_unchanged_inputs(self) -> None:
        for function in (strip_prefix, strip_prefix_legacy):
            for text, prefix in (
                ("value", "missing"),
                ("value", ""),
                ("", "prefix"),
                ("", ""),
                ("ba-value", "ab"),
            ):
                with self.subTest(function=function.__name__, text=text, prefix=prefix):
                    self.assertIs(function(text, prefix), text)

    def test_input_collections_are_not_mutated(self) -> None:
        texts = ["ababvalue", "other", ""]
        prefixes = ["ab", "missing", ""]
        for function in (strip_prefix, strip_prefix_legacy):
            with self.subTest(function=function.__name__):
                self.assertEqual(
                    [function(text, prefix) for text, prefix in zip(texts, prefixes)],
                    ["abvalue", "other", ""],
                )
                self.assertEqual(texts, ["ababvalue", "other", ""])
                self.assertEqual(prefixes, ["ab", "missing", ""])

    def test_preserves_runtime_error_and_short_circuit_behavior(self) -> None:
        for function in (strip_prefix, strip_prefix_legacy):
            with self.subTest(function=function.__name__):
                with self.assertRaises(TypeError):
                    function("value", 1)
                with self.assertRaises(AttributeError):
                    function(None, "prefix")
                self.assertIsNone(function(None, ""))


if __name__ == "__main__":
    unittest.main()
