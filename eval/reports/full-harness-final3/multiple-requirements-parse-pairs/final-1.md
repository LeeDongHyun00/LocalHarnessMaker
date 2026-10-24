Repaired `parse_pairs`, added its public specification docstring, and added five regression tests. Duplicate keys retain their original order, and input text remains unchanged.

Verification passed:
- `python -m py_compile solution.py test_solution.py`
- `python -m unittest discover -v` — all 5 tests passed.