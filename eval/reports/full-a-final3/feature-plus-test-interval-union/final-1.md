Implemented `union` with sorted merging of overlapping or touching intervals, `ValueError` for reversed endpoints, and input preservation.

Added five unittest methods covering ordinary, boundary, empty, and invalid inputs.

Verified with `python -m unittest discover -v`: all 5 tests passed.