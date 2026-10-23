Fixed `normalize` to convert CRLF and lone CR to LF while preserving existing LF, other characters, and trailing newlines. Its signature and type hints are unchanged.

Added a regression test in `test_solution.py`. `python -m unittest discover -v` passed (1 test).