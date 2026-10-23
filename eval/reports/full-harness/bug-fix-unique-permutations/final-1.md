Fixed `permutations` to return distinct permutations in sorted lexicographic order, including `[""]` for empty input. Preserved its signature and type hints.

Added two regression tests in `test_solution.py`. Compilation and `python -m unittest discover -v` both pass.