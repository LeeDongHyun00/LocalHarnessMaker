Fixed `prefix` to return inclusive prefix sums, preserving input length, values, and order. Added the public specification docstring and five regression tests covering empty input, single elements, negatives, zeros, and input preservation.

Verified with `python -m unittest discover -v`: all 5 tests pass.