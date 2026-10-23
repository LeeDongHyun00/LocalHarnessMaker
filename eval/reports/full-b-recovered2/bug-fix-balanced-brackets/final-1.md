Fixed `balanced` to validate nesting of `()`, `[]`, and `{}`, ignore other characters, and accept empty text. Signature and type hints are preserved.

Added two regression test methods in `test_solution.py`. Both pass with `python -m unittest discover -v` on Python 3.13.5.