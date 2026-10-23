import unittest

from solution import strip_prefix, strip_prefix_legacy


class StripPrefixTests(unittest.TestCase):
    def test_removes_exactly_one_matching_prefix(self) -> None:
        for function in (strip_prefix, strip_prefix_legacy):
            for text, prefix, expected in (
                ("prefix-value", "prefix-", "value"),
                ("ababvalue", "ab", "abvalue"),
                ("same", "same", ""),
                ("abacus", "abc", "abacus"),
            ):
                with self.subTest(function=function.__name__, text=text, prefix=prefix):
                    self.assertEqual(function(text, prefix), expected)

    def test_nonmatching_and_empty_prefixes_leave_text_unchanged(self) -> None:
        for function in (strip_prefix, strip_prefix_legacy):
            for text, prefix in (
                ("value", "other"),
                ("value", ""),
                ("", "prefix"),
                ("", ""),
                ("ab", "abcd"),
            ):
                with self.subTest(function=function.__name__, text=text, prefix=prefix):
                    self.assertEqual(function(text, prefix), text)

    def test_inputs_are_unchanged(self) -> None:
        inputs = [["prefix-value", "prefix-"], ["ababvalue", "ab"]]
        original = [pair.copy() for pair in inputs]
        for function in (strip_prefix, strip_prefix_legacy):
            with self.subTest(function=function.__name__):
                self.assertEqual(
                    [function(text, prefix) for text, prefix in inputs],
                    ["value", "abvalue"],
                )
                self.assertEqual(inputs, original)

    def test_invalid_inputs_preserve_error_behavior(self) -> None:
        for function in (strip_prefix, strip_prefix_legacy):
            with self.subTest(function=function.__name__):
                with self.assertRaises(TypeError):
                    function("value", 1)
                with self.assertRaises(AttributeError):
                    function(None, "prefix")
                # An empty prefix short-circuits before accessing text methods.
                self.assertIsNone(function(None, ""))


if __name__ == "__main__":
    unittest.main()
