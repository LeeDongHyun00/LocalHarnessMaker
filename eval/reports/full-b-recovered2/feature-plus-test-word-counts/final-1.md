Implemented `words` with arbitrary whitespace splitting, Unicode casefolding, punctuation preservation, and `{}` for empty input.

Added 6 unittest methods in `test_solution.py` covering ordinary, boundary, Unicode, and empty inputs.

Verified: `python -m unittest discover -v` — all 6 tests pass.