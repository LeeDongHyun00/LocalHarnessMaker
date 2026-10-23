Both functions now delegate to one private helper, preserving signatures, type hints, return types, error behavior, imports, public names, and input immutability.

Added six public API tests covering shared counts, zero and negative totals, empty inputs, immutability, and errors.

`python -m unittest discover -v` passes all six tests on Python 3.13.5.