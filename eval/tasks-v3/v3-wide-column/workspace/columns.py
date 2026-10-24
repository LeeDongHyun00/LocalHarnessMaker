from glyph_width import display_width


def wrap(text: str, width: int) -> list[str]:
    if width < 1:
        raise ValueError('width')
    lines: list[str] = []
    current = ''
    used = 0
    for char in text:
        if char == '\n':
            lines.append(current)
            current, used = '', 0
            continue
        size = display_width(char)
        if size > width:
            raise ValueError('glyph')
        if used + size > width:
            lines.append(current)
            current, used = '', 0
        current += char
        used += size
    lines.append(current)
    return lines


def render(rows: list[list[str]], widths: list[int]) -> str:
    if any(w < 1 for w in widths):
        raise ValueError('width')
    output: list[str] = []
    for row in rows:
        if len(row) != len(widths):
            raise ValueError('arity')
        cells = [wrap(text, width) for text, width in zip(row, widths)]
        for index in range(max(map(len, cells), default=0)):
            parts = []
            for lines, width in zip(cells, widths):
                fragment = lines[index] if index < len(lines) else ''
                parts.append(fragment + ' ' * (width - len(fragment)))
            output.append(' | '.join(parts))
    return '\n'.join(output)
