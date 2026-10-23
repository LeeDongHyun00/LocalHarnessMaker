Fixed `ordinal` to handle 11–13 endings and reject negatives. Added the public specification docstring and five regression tests covering suffixes, zero, negatives, and preservation of input values and collection order.

Verified with `python -m unittest discover -v`: all 5 tests pass.