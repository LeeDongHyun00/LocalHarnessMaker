Fixed `balanced` to validate nesting of `()`, `[]`, and `{}`, ignore other characters, and accept empty text. Preserved its signature and type hints.

Added regression coverage in `test_solution.py`. Compilation and `python -m unittest discover -v` both passed.