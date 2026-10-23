Implemented `select` with ordered, deduplicated columns, omitted missing keys, preserved values, and new dictionaries without modifying inputs.

Added 7 tests in `test_solution.py` covering ordinary, boundary, and empty inputs.

Verified with `python -m unittest discover -v`: **all 7 tests passed**.