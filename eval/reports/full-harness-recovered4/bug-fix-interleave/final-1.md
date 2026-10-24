Fixed `interleave` to append the longer input’s remainder while preserving its signature, type hints, and input collections.

Added regression coverage for unequal lengths, equal lengths, and empty inputs.

Verified compilation and `python -m unittest discover -v`: 1 test passed.