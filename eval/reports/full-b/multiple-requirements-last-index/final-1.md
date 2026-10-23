Fixed `last_index` to return the last matching index without changing input values or order. Preserved type hints, added the public specification docstring, and added six regression tests.

Verified with `python -m unittest discover -v`: all 6 tests pass.