from typing import BinaryIO

def append(stream: BinaryIO, payload: bytes) -> None:
    if len(payload) > 65535:
        raise ValueError('oversize')
    data = len(payload).to_bytes(2, 'little') + payload + bytes([sum(payload) % 256])
    while data:
        written = stream.write(data)
        if written is None or written <= 0 or written > len(data):
            raise OSError('short write')
        data = data[written:]

def replay(stream: BinaryIO) -> list[bytes]:
    data = stream.read()
    result = []
    offset = 0
    while len(data) - offset >= 2:
        size = int.from_bytes(data[offset:offset + 2], 'little')
        end = offset + 2 + size + 1
        if end > len(data):
            break
        payload = data[offset + 2:end - 1]
        if sum(payload) % 256 != data[end - 1]:
            raise ValueError(f'checksum at {offset}')
        result.append(payload)
        offset = end
    return result
