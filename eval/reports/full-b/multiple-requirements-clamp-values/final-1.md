Repaired `clamp` in [solution.py](solution.py), retained type hints, and added its public specification as a docstring.

Added six regression tests in [test_solution.py](test_solution.py), covering inclusive and equal bounds, reversed bounds, input preservation, and collection order.

`python -m unittest discover -v` passes all six tests on Python 3.13.5.