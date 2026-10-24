Fixed `flatten` to include every element from each inner list in order, skipping empty lists without mutating inputs. Preserved its signature and type hints.

Added two regression tests in `test_solution.py`. Compilation succeeded, and `python -m unittest discover -v` passed both tests.