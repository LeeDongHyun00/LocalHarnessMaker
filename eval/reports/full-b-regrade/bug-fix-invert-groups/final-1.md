Fixed `invert` to group keys by value in insertion order without mutating the input. Signature and type hints are unchanged.

Added tests for repeated values, input preservation, and empty input. `python -m unittest discover -v` passes: 2 tests.