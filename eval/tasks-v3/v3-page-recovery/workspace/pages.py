import json
import struct
import zlib
from pathlib import Path

from page_format import encode_page

class Store:
    def __init__(self, path: str | Path) -> None:
        self.path=Path(path)
        self.slots: dict[str,str]={}
        self.next=0
    def append(self, text: str) -> int:
        slot=self.next
        self.slots[str(slot)]=text
        self.next+=1
        return slot
    def get(self, slot: int) -> str:
        return self.slots[str(slot)]
    def delete(self, slot: int) -> None:
        del self.slots[str(slot)]
    def commit(self) -> None:
        self.path.write_bytes(encode_page({'next':self.next,'slots':self.slots}))
