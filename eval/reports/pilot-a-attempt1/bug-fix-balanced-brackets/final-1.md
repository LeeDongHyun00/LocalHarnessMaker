Fixed `balanced` to validate nesting of `()`, `[]`, and `{}`, ignore other characters, and reject unmatched brackets. Its signature and type hints are preserved.

Added regression cases in `test_solution.py`.

Verified: `python -m unittest discover -v` passes.