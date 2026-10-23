Fixed `normalize` to convert CRLF and lone CR to LF while preserving all other characters and trailing newlines. Added its public specification as a docstring and four regression tests covering input preservation and collection order.

Verified with `python -m unittest discover -v`: all 4 tests pass.