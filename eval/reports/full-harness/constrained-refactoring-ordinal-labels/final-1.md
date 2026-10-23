Refactored both public functions to delegate to `_format_ordinal`, preserving signatures, type hints, formatting, and error behavior.

Added two public API tests covering suffixes, zero, teen exceptions, and negative inputs.

Validation passed:
- `python -m py_compile solution.py`
- `python -m unittest discover -v` — 2 tests passed.