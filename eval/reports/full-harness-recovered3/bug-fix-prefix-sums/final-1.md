Fixed `prefix` to return inclusive prefix sums while preserving its signature, type hints, and input collection.

Added a regression test covering positive and negative numbers, empty input, preserved length, and input immutability.

Both checks passed:
- `python -m py_compile solution.py`
- `python -m unittest discover -v`