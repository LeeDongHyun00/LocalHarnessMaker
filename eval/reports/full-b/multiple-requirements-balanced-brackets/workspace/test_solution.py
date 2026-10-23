import unittest

from solution import balanced


class BalancedTests(unittest.TestCase):
    def test_empty_text_is_balanced(self) -> None:
        self.assertTrue(balanced(""))

    def test_matching_pairs_and_nesting(self) -> None:
        for text in ("()", "[]", "{}", "()[]{}", "{[()]}", "([]{()})"):
            with self.subTest(text=text):
                self.assertTrue(balanced(text))

    def test_closing_brackets_must_match_the_latest_opening(self) -> None:
        for text in (")(", "][", "}{", "([)]", "{[}]", "(]", "[}", "{)"):
            with self.subTest(text=text):
                self.assertFalse(balanced(text))

    def test_unmatched_opening_or_closing_brackets(self) -> None:
        cases = (
            "(", "[", "{", ")", "]", "}",
            "(()", "())", "[[]", "[]]", "{{}", "{}}", "([]){",
        )
        for text in cases:
            with self.subTest(text=text):
                self.assertFalse(balanced(text))

    def test_other_characters_are_ignored(self) -> None:
        cases = (
            "plain text 123 <>=!", "한글 🙂", "a{b[c(d)e]f}g", "(\n[\ttext]\n)",
        )
        for text in cases:
            with self.subTest(text=text):
                self.assertTrue(balanced(text))
        self.assertFalse(balanced("text [with an unclosed bracket"))
        self.assertFalse(balanced("text with a stray } bracket"))

    def test_preserves_input_values_and_order(self) -> None:
        texts = ["{a[b(c)]}", ")(", "", "[text", "()[]{}"]
        original = texts.copy()

        results = [balanced(text) for text in texts]

        self.assertEqual(results, [True, False, True, False, True])
        self.assertEqual(texts, original)


if __name__ == "__main__":
    unittest.main()
