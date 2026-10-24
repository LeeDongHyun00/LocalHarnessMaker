Fix nested transaction ownership in unitwork.py. The connection is a caller-owned
sqlite3 connection opened with isolation_level=None, with no transaction active.
Use one UnitOfWork(connection) object recursively as a context manager; __enter__
returns that object, and __exit__ must never suppress an exception (any false
return value is permitted).

TX1. The outermost entry starts BEGIN; a normal outer exit commits and an exceptional
outer exit rolls back. The connection remains open and reusable after either.
TX2. Every nested entry creates a distinct SAVEPOINT. A normal nested exit releases
only that savepoint. An exceptional nested exit rolls back to and releases only
that savepoint. If the caller catches the inner exception inside the outer block,
outer changes and later changes still commit. Uncaught exceptions unwind all levels.
TX3. Three or more levels and sibling nested blocks must work. The depth returns to
zero after unwinding, and the same object may start another independent transaction.
Do not replace the connection, commit a parent early or issue a full rollback for
an inner failure. All statements issued by the caller keep their original order.

Use Python 3.11+ and the standard library. Preserve the documented public API.
Run `python -m unittest discover -s . -p "test_*.py" -v` from workspace/.
Change application code and add regression tests as needed.
