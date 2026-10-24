Fixed `normalize` without changing its signature or type hints. CRLF and lone CR now become LF, preserving all other characters and trailing line breaks.

Added a regression test covering mixed endings, repeated breaks, and unchanged text.

Validation passed: compilation and `python -m unittest discover -v` (1 test).