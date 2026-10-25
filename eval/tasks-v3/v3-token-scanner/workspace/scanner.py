from token_api import Token

def scan(text: str) -> list[Token]:
    remaining = text
    offset = 0
    result = []
    while remaining:
        ch = remaining[0]
        if ch.isspace():
            size = 1
        elif ch == '"':
            size = 1
            value = []
            while size < len(remaining) and remaining[size] != '"':
                ch = remaining[size]
                if ch == '\\':
                    size += 1
                    if size == len(remaining):
                        raise ValueError(f'unterminated at {offset}')
                    ch = remaining[size]
                value.append(ch)
                size += 1
            if size == len(remaining):
                raise ValueError(f'unterminated at {offset}')
            size += 1
            result.append(Token('string', ''.join(value), offset, offset + size))
        else:
            size = 1
            if ch.isascii() and (ch.isalpha() or ch == '_'):
                kind = 'word'
                while size < len(remaining) and remaining[size].isascii() and (remaining[size].isalnum() or remaining[size] == '_'):
                    size += 1
            elif ch in '0123456789':
                kind = 'number'
                while size < len(remaining) and remaining[size] in '0123456789':
                    size += 1
            else:
                kind = 'punct'
            result.append(Token(kind, remaining[:size], offset, offset + size))
        remaining = remaining[size:]
        offset += size
    return result
