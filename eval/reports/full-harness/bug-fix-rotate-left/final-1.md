Fixed `rotate` to normalize steps modulo length and handle empty input, preserving its signature, type hints, and input collection.

Added two regression tests covering positive, negative, zero, and full-length rotations, empty input, and input preservation.

Both checks passed:
- `python -m unittest discover -v`
- `python -m py_compile solution.py test_solution.py`