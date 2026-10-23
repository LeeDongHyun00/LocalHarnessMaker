Implemented `strip_prefix` to remove exactly one matching prefix, leaving text unchanged for empty or nonmatching prefixes.

Added four unittest methods in `test_solution.py` covering ordinary, repeated-prefix, boundary, Unicode, and empty inputs.

`python -m unittest discover -v` passes all 4 tests.