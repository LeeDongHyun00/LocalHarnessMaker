Fixed `strip_prefix` to remove exactly one complete matching prefix, preserving type hints. Added its public specification docstring and four regression tests covering empty/nonmatching prefixes, repeated prefixes, input preservation, and collection order.

Verification passed:

- `python -m py_compile solution.py`
- `python -m unittest discover -v` — all 4 tests passed.