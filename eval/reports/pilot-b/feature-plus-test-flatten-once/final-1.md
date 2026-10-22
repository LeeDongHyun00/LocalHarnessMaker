Implemented `flatten` to flatten exactly one level, preserve order, ignore empty inner lists, and return a new list without mutating inputs. Type hints are retained.

Added 6 unittest methods covering ordinary, boundary, empty, nested, and mutation cases.

Verified with `python -m unittest discover -v`: all 6 tests pass.