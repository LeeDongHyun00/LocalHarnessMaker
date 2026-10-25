import json
import re

class CatalogError(ValueError):
    def __init__(self, code: str, line: int, column: int) -> None:
        self.code, self.line, self.column = code, line, column
        super().__init__(f'{code}:{line}:{column}')

def parse_rows(source: str) -> list[tuple]:
    rows: list[tuple] = []
    pattern = re.compile(r'\s*([A-Za-z_][A-Za-z_0-9]*)\[([a-z]+)\]\s*=\s*(.*)')
    for line, text in enumerate(source.splitlines(), 1):
        if not text.strip() or text.lstrip().startswith('#'):
            continue
        column = len(text) - len(text.lstrip()) + 1
        match = pattern.fullmatch(text)
        if match is None:
            raise CatalogError('syntax', line, column)
        key, form, literal = match.groups()
        try:
            value = json.loads(literal)
        except (ValueError, TypeError):
            raise CatalogError('syntax', line, column) from None
        if not isinstance(value, str):
            raise CatalogError('syntax', line, column)
        rows.append((key,form,value,line,match.start(1)+1,match.start(2)+1))
    return rows

def compile_catalog(source: str, forms: tuple[str, ...]) -> dict[str,dict[str,str]]:
    catalog: dict[str,dict[str,str]] = {}
    for key,form,value,*_ in parse_rows(source):
        catalog.setdefault(key, {})[form] = value
    return catalog
