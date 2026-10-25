import json
import struct
import zlib

def encode_page(state: dict, version: int = 2) -> bytes:
    payload=json.dumps(state,sort_keys=True,separators=(',', ':'),ensure_ascii=True).encode()
    return b'SLOT'+bytes([version])+struct.pack('>HI',len(payload),zlib.crc32(payload))+payload+bytes(501-len(payload))

