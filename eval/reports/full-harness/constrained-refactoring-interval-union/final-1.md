Refactored `union` and `union_legacy` to delegate to private `_union`, preserving signatures, type hints, return types, error behavior, and input immutability.

Added three passing tests covering both APIs: merging and sorting, empty input, invalid intervals, and input preservation.

Verification passed:
- `python -m py_compile solution.py`
- `python -m unittest discover -v`