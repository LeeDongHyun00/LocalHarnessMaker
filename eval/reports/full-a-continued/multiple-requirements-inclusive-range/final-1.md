Fixed `inclusive` to include both endpoints in ascending or descending order and return a singleton for equal endpoints. Added the public specification docstring, retained type hints, and added five regression tests covering ordering and input preservation.

`python -m unittest discover -v` passed all 5 tests.