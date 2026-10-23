import unittest

from solution import invert


class InvertTests(unittest.TestCase):
    def test_groups_repeated_values_in_insertion_order(self):
        items = {"zebra": "shared", "middle": "unique", "apple": "shared"}
        original = items.copy()

        self.assertEqual(
            invert(items),
            {"shared": ["zebra", "apple"], "unique": ["middle"]},
        )
        self.assertEqual(items, original)

    def test_empty_input(self):
        self.assertEqual(invert({}), {})


if __name__ == "__main__":
    unittest.main()
