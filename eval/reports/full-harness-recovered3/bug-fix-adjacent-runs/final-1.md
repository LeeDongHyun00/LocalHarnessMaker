Fixed `runs` to group adjacent equal strings, preserve separate nonadjacent runs, and return `[]` for empty input. Its signature and type hints remain unchanged, and input is not mutated.

Added two regression tests. Both passed with `python -m unittest discover -v`; compilation also passed.