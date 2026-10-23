import unittest

from solution import invert


class InvertTests(unittest.TestCase):
    def test_groups_keys_in_insertion_order_without_mutating_input(self) -> None:
        items = {"z": "shared", "b": "other", "a": "shared"}
        original = items.copy()

        self.assertEqual(invert(items), {"shared": ["z", "a"], "other": ["b"]})
        self.assertEqual(list(items.items()), list(original.items()))

    def test_empty_input(self) -> None:
        self.assertEqual(invert({}), {})


if __name__ == "__main__":
    unittest.main()
