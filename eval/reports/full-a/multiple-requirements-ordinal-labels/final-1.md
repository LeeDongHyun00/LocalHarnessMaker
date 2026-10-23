Fixed `ordinal` to handle 11/12/13 suffix exceptions and reject negatives. Added its public specification as a docstring, retained type hints, and added five regression tests covering zero, large integers, and input/order preservation.

Verified with `python -m unittest discover -v`: all 5 tests passed.