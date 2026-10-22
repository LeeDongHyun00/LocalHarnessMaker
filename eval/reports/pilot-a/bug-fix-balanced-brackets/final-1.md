Fixed `balanced` to validate nesting of `()`, `[]`, and `{}`, ignore other characters, and reject unmatched brackets while preserving its signature and type hints.

Added regression coverage in `test_solution.py`.

Verified with `python -m unittest discover -v`: 1 test passed.