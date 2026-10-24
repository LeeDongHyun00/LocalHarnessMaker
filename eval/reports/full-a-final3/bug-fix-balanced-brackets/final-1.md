Fixed `balanced` to check proper nesting of `()`, `[]`, and `{}`, ignore other characters, and accept empty text. Preserved its signature and type hints.

Added regression coverage in `test_solution.py`.

Verified with `python -m unittest discover -v`: 1 test passed.