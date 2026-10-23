Implemented `normalize` to convert CRLF and lone CR to LF while preserving other characters and trailing newlines.

Added six unittest methods covering ordinary, boundary, and empty inputs.

Verified with `python -m unittest discover -v`: all 6 tests passed.