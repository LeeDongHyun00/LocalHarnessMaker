import unittest

from solution import invert


class InvertTests(unittest.TestCase):
    def test_groups_keys_in_insertion_order_without_mutating_input(self) -> None:
        items = {"third": "shared", "first": "other", "second": "shared"}
        original = items.copy()

        self.assertEqual(
            invert(items),
            {"shared": ["third", "second"], "other": ["first"]},
        )
        self.assertEqual(list(items.items()), list(original.items()))

    def test_empty_input(self) -> None:
        self.assertEqual(invert({}), {})


if __name__ == "__main__":
    unittest.main()
