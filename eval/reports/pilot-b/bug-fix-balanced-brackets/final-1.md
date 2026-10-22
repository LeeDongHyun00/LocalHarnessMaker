Fixed `balanced` to correctly check nesting of `()`, `[]`, and `{}` while preserving its signature and ignoring other characters.

Added one regression test in `test_solution.py` covering 12 cases.

Verified: `python -m unittest discover -v` passes.