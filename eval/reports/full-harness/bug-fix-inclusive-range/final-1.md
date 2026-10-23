Fixed `inclusive` to include both endpoints in ascending and descending order, with a singleton for equal endpoints. Preserved its signature and type hints.

Added a regression test covering both directions, equal endpoints, and negative values.

Both compilation and `python -m unittest discover -v` passed.