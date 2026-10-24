import sqlite3
from types import TracebackType

class UnitOfWork:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.depth = 0

    def __enter__(self) -> 'UnitOfWork':
        if self.depth == 0:
            self.connection.execute('BEGIN')
        else:
            self.connection.execute(f'SAVEPOINT uow_{self.depth}')
        self.depth += 1
        return self

    def __exit__(self, kind: type[BaseException] | None, value: BaseException | None,
                 traceback: TracebackType | None) -> bool:
        self.depth -= 1
        if self.depth == 0:
            self.connection.execute('ROLLBACK' if kind else 'COMMIT')
        else:
            name = f'uow_{self.depth}'
            if kind:
                self.connection.execute('ROLLBACK')
            self.connection.execute(f'RELEASE {name}')
        return False
