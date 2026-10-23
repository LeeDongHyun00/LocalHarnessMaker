import unittest

from solution import unique


class UniqueTests(unittest.TestCase):
    def test_preserves_first_occurrence_order_and_input(self) -> None:
        items = ["b", "a", "b", "A", "a", "c"]
        original = items.copy()

        self.assertEqual(unique(items), ["b", "a", "A", "c"])
        self.assertEqual(items, original)

    def test_empty_input(self) -> None:
        self.assertEqual(unique([]), [])


if __name__ == "__main__":
    unittest.main()
