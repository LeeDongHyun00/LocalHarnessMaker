Fixed `inclusive` to include both endpoints, step in either direction, and return a singleton for equal endpoints. Added the public specification docstring, preserved type hints, and added six regression tests covering order and unchanged inputs.

Verified with `python -m unittest discover -v` on Python 3.13.5: all six tests pass.