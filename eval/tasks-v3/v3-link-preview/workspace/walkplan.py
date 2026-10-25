from dataclasses import dataclass
import os
from pathlib import Path
from typing import Iterator

@dataclass(frozen=True)
class Entry:
    path: str
    kind: str

@dataclass(frozen=True)
class LinkPlan:
    path: str
    target: str
    status: str

def walk(root: str | Path) -> Iterator[Entry]:
    base = Path(root)
    entries: list[Entry] = []
    def visit(folder: Path) -> None:
        for child in folder.iterdir():
            relative = child.relative_to(base).as_posix()
            if child.is_symlink():
                entries.append(Entry(relative, 'link'))
            elif child.is_dir():
                entries.append(Entry(relative, 'directory'))
                visit(child)
            else:
                entries.append(Entry(relative, 'file'))
    visit(base)
    yield from sorted(entries, key=lambda entry: entry.path)

def preview_links(root: str | Path) -> list[LinkPlan]:
    raise NotImplementedError('link preview')
