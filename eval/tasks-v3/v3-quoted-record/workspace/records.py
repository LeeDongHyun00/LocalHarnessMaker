from dataclasses import dataclass

@dataclass
class Record:
    fields: list[str]
    start: int
    end: int

class ParseError(ValueError):
    def __init__(self, offset: int) -> None:
        super().__init__('csv')
        self.offset = offset

class Reader:
    def __init__(self, text: str) -> None:
        self.text = text
        self.cursor = 0

    def _error(self, offset: int) -> None:
        newline = self.text.find('\n', offset)
        self.cursor = len(self.text) if newline == -1 else newline + 1
        raise ParseError(offset)

    def read(self) -> Record | None:
        text = self.text
        if self.cursor == len(text):
            return None
        start = self.cursor
        fields: list[str] = []
        field = ''
        mode = 'start'
        while self.cursor < len(text):
            i = self.cursor
            c = text[i]
            if mode == 'quoted':
                self.cursor += 1
                if c == '"':
                    mode = 'closed'
                else:
                    field += '\n' if c == '\r' else c
                continue
            if mode == 'closed' and c == '"':
                field += c
                mode = 'quoted'
                self.cursor += 1
                continue
            terminator = 2 if text.startswith('\r\n', i) else 1 if c == '\n' else 0
            if c == ',' or terminator:
                fields.append(field)
                self.cursor += terminator or 1
                if terminator:
                    return Record(fields, start, i)
                field, mode = '', 'start'
                continue
            if mode == 'closed':
                self._error(i)
            if c == '"':
                if mode != 'start':
                    self._error(i)
                mode = 'quoted'
            else:
                field += c
                mode = 'plain'
            self.cursor += 1
        if mode == 'quoted':
            self._error(len(text))
        fields.append(field)
        return Record(fields, start, len(text))
