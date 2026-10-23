Fixed `prefix` to return inclusive sums, preserving its signature and leaving inputs unchanged.

Added regression coverage in `test_solution.py` for empty, singleton, positive, and negative inputs.

Verified on Python 3.13.5: `python -m unittest discover -v` passes (1 test).