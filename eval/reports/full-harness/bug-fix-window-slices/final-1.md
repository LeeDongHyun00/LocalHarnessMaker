Fixed `windows` to return overlapping, full-size windows, reject nonpositive sizes, and return `[]` for oversized windows. Preserved its signature, type hints, and input contents.

Added three regression tests in `test_solution.py`. Compilation and `python -m unittest discover -v` both passed.