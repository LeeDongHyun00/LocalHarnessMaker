Implemented `union` with sorted interval merging, touching-endpoint support, `ValueError` validation, and input preservation. Type hints retained.

Added six unittest methods covering ordinary, boundary, empty, and invalid inputs.

Verified: `python -m unittest discover -v` — all 6 tests pass on Python 3.13.5.