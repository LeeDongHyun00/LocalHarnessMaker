Fixed `common` to return the longest case-sensitive common prefix while preserving its signature, type hints, and input collections.

Added a regression test covering empty input, single items, shared prefixes, case sensitivity, and input preservation.

Both checks passed:

- `python -m py_compile solution.py`
- `python -m unittest discover -v`