Fixed `flatten` to flatten exactly one level, preserve values and order, ignore empty lists, and return a new list without mutating inputs. Added its public docstring and five regression tests in `test_solution.py`.

Verified on Python 3.13.5: `python -m unittest discover -v` passes all five tests.