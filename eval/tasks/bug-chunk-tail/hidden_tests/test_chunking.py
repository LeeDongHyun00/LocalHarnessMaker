"""Private grading checks; copy into a grading workspace after execution."""

import unittest

from chunking import chunked


class ChunkingTests(unittest.TestCase):
    def test_single_item(self) -> None:
        self.assertEqual(chunked([8], 4), [[8]])

    def test_partial_tail_and_input_preservation(self) -> None:
        items = [2, 4, 6, 8, 10]
        self.assertEqual(chunked(items, 2), [[2, 4], [6, 8], [10]])
        self.assertEqual(items, [2, 4, 6, 8, 10])

    def test_unit_chunks_and_empty_input(self) -> None:
        self.assertEqual(chunked([3, 5, 7], 1), [[3], [5], [7]])
        self.assertEqual(chunked([], 2), [])


if __name__ == "__main__":
    unittest.main()
