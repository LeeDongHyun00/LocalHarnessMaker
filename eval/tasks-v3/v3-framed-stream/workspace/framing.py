from collections.abc import Callable

TERMINATOR = b'\r\n.\r\n'

class Decoder:
    def __init__(self, on_frame: Callable[[bytes], None], on_error: Callable[[str], None]) -> None:
        self.on_frame = on_frame
        self.on_error = on_error
        self.pending = bytearray()

    def feed(self, data: bytes) -> None:
        self.pending.extend(data)
        while True:
            boundary = self.pending.find(TERMINATOR, max(0, len(self.pending) - len(data)))
            if boundary == -1:
                return
            payload = bytes(self.pending[:boundary])
            del self.pending[:boundary + len(TERMINATOR)]
            if b'\x00' in payload:
                self.on_error('nul')
            else:
                self.on_frame(payload)

    def finish(self) -> None:
        if self.pending:
            raise ValueError('truncated')
