from collections.abc import Callable

def format_record(level: str, message: str) -> bytes:
    escaped = message.replace('\\','\\\\').replace('\r','\\r').replace('\n','\\n')
    return (level.upper() + ': ' + escaped + '\n').encode('utf-8')

class Sink:
    def __init__(self, send: Callable[[tuple[bytes,...]],None], capacity: int = 3) -> None:
        if type(capacity) is not int or capacity <= 0: raise ValueError('capacity')
        self.send = send
        self.capacity = capacity
        self.pending = []
    def emit(self, level: str, message: str) -> None:
        if len(self.pending) >= self.capacity: self.flush()
        escaped = message.replace('\\','\\\\').replace('\r','\\r').replace('\n','\\n')
        self.pending.append((level.upper() + ': ' + escaped + '\n').encode('utf-8'))
        if len(self.pending) >= self.capacity: self.flush()
    def flush(self) -> None:
        if self.pending:
            batch = tuple(self.pending)
            self.send(batch)
            del self.pending[:len(batch)]
