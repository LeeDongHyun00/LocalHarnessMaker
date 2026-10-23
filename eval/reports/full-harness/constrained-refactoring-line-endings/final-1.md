Refactored both public functions to delegate to one private helper, preserving signatures, type hints, return types, and error behavior.

Added three passing tests covering newline normalization, trailing newlines, character preservation, input immutability, and invalid inputs.

Verification passed:
- `python -m py_compile solution.py`
- `python -m unittest discover -v`