import unittest

from solution import common


class CommonTests(unittest.TestCase):
    def test_longest_common_prefix(self):
        self.assertEqual(common(["flower", "flow", "flight"]), "fl")
        self.assertEqual(common(["prefix", "pre", "prepare"]), "pre")
        self.assertEqual(common(["same", "same"]), "same")

    def test_empty_and_single_item_inputs(self):
        self.assertEqual(common([]), "")
        self.assertEqual(common(["only item"]), "only item")
        self.assertEqual(common([""]), "")

    def test_empty_strings_and_no_common_prefix(self):
        self.assertEqual(common(["abc", "", "abd"]), "")
        self.assertEqual(common(["", "abc"]), "")
        self.assertEqual(common(["dog", "racecar", "car"]), "")

    def test_case_sensitive_character_matching(self):
        self.assertEqual(common(["Flower", "flower"]), "")
        self.assertEqual(common(["abC", "abc"]), "ab")
        self.assertEqual(common(["\uac00\ub098\ub2e4", "\uac00\ub098\ub77c"]), "\uac00\ub098")

    def test_input_values_and_order_are_preserved(self):
        for items in (["flight", "flower", "flow", "flower"],
                      ["zebra", "apple", "zebra"], [], ["single"]):
            with self.subTest(items=items):
                original = items.copy()
                common(items)
                self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
