import unittest

from solution import common


class CommonTests(unittest.TestCase):
    def test_longest_common_prefix(self) -> None:
        cases = [
            ([], ""),
            (["solo"], "solo"),
            (["flower", "flow", "flight"], "fl"),
            (["prefix", "pre"], "pre"),
            (["same", "same"], "same"),
            (["Case", "case"], ""),
            (["text", ""], ""),
            (["", "text"], ""),
        ]
        for items, expected in cases:
            with self.subTest(items=items):
                original = items.copy()
                self.assertEqual(common(items), expected)
                self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
