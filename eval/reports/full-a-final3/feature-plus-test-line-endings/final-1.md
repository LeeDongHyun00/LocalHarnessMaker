Implemented `normalize` to convert CRLF and lone CR to LF while preserving all other characters and trailing newlines.

Added 3 unittest methods covering ordinary, boundary, and empty inputs.

Verified with `python -m unittest discover -v`: all 3 tests pass.