Fixed `normalize` to convert CRLF and lone CR to LF while preserving existing LF, other characters, and trailing newlines. The signature and type hints remain unchanged.

Added one regression test in `test_solution.py` covering five cases.

Verified: `python -m unittest discover -v` passes.