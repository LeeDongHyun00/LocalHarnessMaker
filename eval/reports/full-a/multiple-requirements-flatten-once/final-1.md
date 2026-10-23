Fixed `flatten` to flatten exactly one level, preserve values and order, skip empty lists, and return a new list without mutating inputs. Preserved type hints and added the public specification as a docstring.

Added four regression tests in `test_solution.py`. All pass with `python -m unittest discover -v`.