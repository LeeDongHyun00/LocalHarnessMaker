Repaired `normalize` and added its public specification as a docstring, preserving the typed API.

Added four regression tests covering newline conversion, trailing and consecutive breaks, character preservation, and unchanged input values and collection order.

Both checks passed:

- `python -m py_compile solution.py`
- `python -m unittest discover -v` — 4 tests passed.