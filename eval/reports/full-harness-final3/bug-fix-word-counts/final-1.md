Fixed `words` to split on arbitrary whitespace, casefold and count tokens, preserve punctuation, and return `{}` for empty input. Its signature and type hints are unchanged.

Added two regression tests in `test_solution.py`. Compilation and `python -m unittest discover -v` both pass.