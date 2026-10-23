Repaired `permutations` to return distinct permutations in lexicographic order, including `[""]` for empty input. Preserved type hints and input values, documented the public specification, and added seven regression tests.

Verification passed:
- `python -m py_compile solution.py`
- `python -m unittest discover -v` — all 7 tests passed.