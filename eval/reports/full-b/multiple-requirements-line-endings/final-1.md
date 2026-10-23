Repaired `normalize` to convert CRLF and lone CR to LF while preserving other characters, line-break counts, and trailing newlines.

Added its public specification docstring and 7 regression tests covering preservation of input values and order.

Verified: `python -m unittest discover -v` — all 7 tests pass.