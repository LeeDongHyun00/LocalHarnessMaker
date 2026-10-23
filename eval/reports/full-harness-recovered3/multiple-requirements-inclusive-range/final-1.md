Fixed `inclusive` to include both endpoints, step in either direction, and return a singleton for equal endpoints. Added a public specification docstring, retained type hints, and added five regression tests covering order and input preservation.

Both checks passed:

- `python -m py_compile solution.py`
- `python -m unittest discover -v` — 5 tests passed.