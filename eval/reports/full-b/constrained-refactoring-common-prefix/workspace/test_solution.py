import unittest

from solution import common, common_legacy


class CommonTests(unittest.TestCase):
    def test_longest_common_prefix(self) -> None:
        cases = [
            (["flower", "flow", "flight"], "fl"),
            (["prefix", "pre", "prefixes"], "pre"),
            (["dog", "racecar", "car"], ""),
            (["same", "same"], "same"),
            (["😀alpha", "😀alpine"], "😀alp"),
        ]
        for function in (common, common_legacy):
            for items, expected in cases:
                with self.subTest(function=function.__name__, items=items):
                    self.assertEqual(function(items), expected)

    def test_empty_and_single_item_inputs(self) -> None:
        for function in (common, common_legacy):
            for items in ([], [""], ["single"], ["flower", "", "flow"]):
                with self.subTest(function=function.__name__, items=items):
                    expected = items[0] if len(items) == 1 else ""
                    self.assertEqual(function(items), expected)
                    if len(items) == 1:
                        self.assertIs(function(items), items[0])

    def test_matching_is_case_sensitive(self) -> None:
        cases = [
            (["Flower", "flow"], ""),
            (["prefixA", "prefixa"], "prefix"),
            (["Aa", "Ab"], "A"),
        ]
        for function in (common, common_legacy):
            for items, expected in cases:
                with self.subTest(function=function.__name__, items=items):
                    self.assertEqual(function(items), expected)

    def test_inputs_are_not_mutated(self) -> None:
        for function in (common, common_legacy):
            with self.subTest(function=function.__name__):
                items = ["flower", "flight", "flow"]
                original = items.copy()
                self.assertEqual(function(items), "fl")
                self.assertEqual(items, original)

    def test_invalid_elements_preserve_errors_and_input(self) -> None:
        cases = [
            (["flower", None], AttributeError),
            ([1, "flower"], TypeError),
            (["a", "b", None], AttributeError),
            (["", None], AttributeError),
        ]
        for function in (common, common_legacy):
            for items, error in cases:
                with self.subTest(function=function.__name__, items=items):
                    original = items.copy()
                    with self.assertRaises(error):
                        function(items)
                    self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
