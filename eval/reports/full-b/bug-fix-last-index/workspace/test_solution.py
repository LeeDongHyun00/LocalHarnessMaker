import unittest

from solution import last_index


class LastIndexTests(unittest.TestCase):
    def test_last_index(self) -> None:
        cases = [
            (["a", "b", "a"], "a", 2),
            (["a", "b"], "a", 0),
            (["a", "b"], "c", None),
            ([], "a", None),
            (["A", "a", "A"], "a", 1),
            (["A"], "a", None),
        ]
        for items, target, expected in cases:
            with self.subTest(items=items, target=target):
                original = items.copy()
                self.assertEqual(last_index(items, target), expected)
                self.assertEqual(items, original)


if __name__ == "__main__":
    unittest.main()
