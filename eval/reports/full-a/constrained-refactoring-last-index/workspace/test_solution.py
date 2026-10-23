import unittest

from solution import last_index, last_index_legacy


class LastIndexTests(unittest.TestCase):
    def test_last_match_and_input_immutability(self) -> None:
        for function in (last_index, last_index_legacy):
            with self.subTest(function=function.__name__):
                items = ["match", "other", "match", "tail"]
                original = items.copy()
                self.assertEqual(function(items, "match"), 2)
                self.assertEqual(items, original)
                self.assertEqual(function(items, "tail"), 3)
                self.assertEqual(function(items, "other"), 1)
                self.assertEqual(items, original)

    def test_empty_absent_case_sensitive_and_zero_index(self) -> None:
        cases = [
            ([], "match", None),
            (["other"], "match", None),
            (["Match"], "match", None),
            (["match", "Match"], "match", 0),
        ]
        for function in (last_index, last_index_legacy):
            for items, target, expected in cases:
                with self.subTest(function=function.__name__, items=items):
                    original = items.copy()
                    self.assertEqual(function(items, target), expected)
                    self.assertEqual(items, original)

    def test_invalid_input_keeps_type_error(self) -> None:
        for function in (last_index, last_index_legacy):
            with self.subTest(function=function.__name__):
                with self.assertRaises(TypeError):
                    function(None, "match")


if __name__ == "__main__":
    unittest.main()
