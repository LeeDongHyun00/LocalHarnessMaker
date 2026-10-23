Fixed `runs` to group adjacent equal strings while keeping nonadjacent occurrences separate. Preserved its signature, type hints, and input.

Added two tests in `test_solution.py`, covering separate runs, empty input, and input preservation.

Verified with `python -m unittest discover -v`: **2 tests passed**.