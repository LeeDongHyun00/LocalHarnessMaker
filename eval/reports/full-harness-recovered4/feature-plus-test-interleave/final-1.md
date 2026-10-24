Implemented `interleave` with type hints, alternating left then right and appending remaining items without mutating inputs.

Added six unittest tests covering ordinary, unequal-length, empty, boundary, and input-preservation cases.

Verified compilation and `python -m unittest discover -v`: all six tests pass.