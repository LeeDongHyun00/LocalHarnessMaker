import tempfile
import unittest
from pathlib import Path
from pages import Store
class PublicSlots(unittest.TestCase):
    def test_in_memory(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            store=Store(Path(folder)/'notes.bin')
            slot=store.append('draft')
            self.assertEqual(store.get(slot),'draft')
