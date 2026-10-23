Repaired `permutations` to return distinct permutations in sorted lexicographic order, including `[""]` for empty input. Preserved type hints and added the public specification docstring.

Added six regression tests covering duplicates, ordering, input preservation, Unicode, and seven-character inputs.

Verification: `python -m unittest discover -v` — all 6 tests passed.