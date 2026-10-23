import unittest

from solution import strip_prefix, strip_prefix_legacy


class StripPrefixTests(unittest.TestCase):
    def test_removes_exactly_one_matching_prefix(self) -> None:
        for function in (strip_prefix, strip_prefix_legacy):
            for text, prefix, expected in (
                ("prefix-value", "prefix-", "value"),
                ("ababvalue", "ab", "abvalue"),
                ("abba", "ab", "ba"),
                ("abc", "abc", ""),
                ("雪雪山", "雪", "雪山"),
            ):
                with self.subTest(function=function.__name__, text=text, prefix=prefix):
                    result = function(text, prefix)
                    self.assertEqual(result, expected)
                    self.assertIsInstance(result, str)

    def test_nonmatching_and_empty_prefix_leave_text_unchanged(self) -> None:
        for function in (strip_prefix, strip_prefix_legacy):
            for text, prefix in (("abba", "ba"), ("abc", ""), ("", "a"), ("", ""), ("ab", "abc")):
                with self.subTest(function=function.__name__, text=text, prefix=prefix):
                    self.assertIs(function(text, prefix), text)

    def test_inputs_are_unchanged(self) -> None:
        texts = ["prefix-value", "prefix-prefix-value", "other"]
        prefixes = ["prefix-", "", "other"]
        original_texts = texts.copy()
        original_prefixes = prefixes.copy()
        for function in (strip_prefix, strip_prefix_legacy):
            for text in texts:
                for prefix in prefixes:
                    function(text, prefix)
            self.assertEqual(texts, original_texts)
            self.assertEqual(prefixes, original_prefixes)

    def test_error_and_short_circuit_behavior_is_preserved(self) -> None:
        for function in (strip_prefix, strip_prefix_legacy):
            with self.subTest(function=function.__name__):
                with self.assertRaises(TypeError):
                    function("abc", 1)
                with self.assertRaises(AttributeError):
                    function(None, "a")
                self.assertIsNone(function(None, ""))
                self.assertEqual(function("abc", None), "abc")


if __name__ == "__main__":
    unittest.main()
