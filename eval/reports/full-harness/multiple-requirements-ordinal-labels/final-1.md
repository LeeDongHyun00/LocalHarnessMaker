Fixed `ordinal` to handle teen exceptions and reject negatives, preserving type hints. Added its public specification docstring and five regression tests covering suffixes, zero, negatives, and input/order preservation.

Verification passed:
- `python -m py_compile solution.py`
- `python -m unittest discover -v` — all 5 tests passed.