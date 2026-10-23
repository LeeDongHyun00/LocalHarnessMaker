"""Tests for both public last-index functions."""

import unittest

from solution import last_index, last_index_legacy


class LastIndexTests(unittest.TestCase):
    def test_returns_last_matching_index(self) -> None:
        for function in (last_index, last_index_legacy):
            for items, target, expected in (
                (["a", "b", "a"], "a", 2),
                (["a", "b", "c"], "b", 1),
                (["a", "b", "c"], "a", 0),
                (["a"], "a", 0),
                (["", "a", ""], "", 2),
            ):
                with self.subTest(function=function.__name__, items=items, target=target):
                    result = function(items, target)
                    self.assertEqual(result, expected)
                    self.assertIs(type(result), int)

    def test_returns_none_for_absent_target_or_empty_input(self) -> None:
        for function in (last_index, last_index_legacy):
            for items in ([], ["a"], ["a", "b", "a"]):
                with self.subTest(function=function.__name__, items=items):
                    self.assertIsNone(function(items, "missing"))

    def test_matching_is_case_sensitive(self) -> None:
        for function in (last_index, last_index_legacy):
            with self.subTest(function=function.__name__):
                self.assertEqual(function(["A", "a", "A"], "a"), 1)
                self.assertIsNone(function(["A"], "a"))

    def test_does_not_mutate_input(self) -> None:
        for function in (last_index, last_index_legacy):
            for target in ("a", "missing"):
                for items in ([], ["a", "b", "a"]):
                    with self.subTest(
                        function=function.__name__, items=items, target=target
                    ):
                        original = items.copy()
                        function(items, target)
                        self.assertEqual(items, original)

    def test_invalid_input_raises_type_error(self) -> None:
        for function in (last_index, last_index_legacy):
            with self.subTest(function=function.__name__):
                with self.assertRaises(TypeError):
                    function(None, "a")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
