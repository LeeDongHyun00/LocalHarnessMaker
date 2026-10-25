from collections.abc import Iterable, Mapping
from typing import Any

def compile_fields(fields: Iterable[tuple]) -> tuple:
    result = []
    names = set()
    for index, (name, width, align) in enumerate(fields):
        if not isinstance(name,str) or not name: raise ValueError(f'field {index}: name')
        if name in names: raise ValueError(f'field {index}: duplicate')
        if type(width) is not int or width <= 0: raise ValueError(f'field {index}: width')
        if align not in ('L','R'): raise ValueError(f'field {index}: align')
        names.add(name); result.append((name,width,align))
    return tuple(result)

def render_rows(fields: Iterable[tuple], rows: Iterable[Mapping[str, Any]]) -> list[str]:
    result = []
    for row in rows:
        plan = compile_fields(fields)
        cells = []
        for name,width,align in plan:
            value = str(row.get(name,''))[:width]
            cells.append(value.ljust(width) if align == 'L' else value.rjust(width))
        result.append(''.join(cells))
    return result
