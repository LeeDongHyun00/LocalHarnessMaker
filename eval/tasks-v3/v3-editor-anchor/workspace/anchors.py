from collections.abc import Iterable

def transform(cursor: int, edits: Iterable[tuple]) -> int:
    for edit in edits:
        if edit[0] == 'insert' and edit[1] < cursor:
            cursor += len(edit[2])
    return cursor

def transform_many(cursors: Iterable[int], edits: Iterable[tuple]) -> list[int]:
    return [transform(c, edits) for c in cursors]
