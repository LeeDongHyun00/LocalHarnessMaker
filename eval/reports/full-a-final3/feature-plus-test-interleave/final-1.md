Implemented `interleave` with left-first alternation, ordered remainders, empty-input support, preserved type hints, and no input mutation.

Added five unittest methods covering ordinary, boundary, empty, and non-mutation cases.

Verified with `python -m unittest discover -v`: all 5 tests passed.