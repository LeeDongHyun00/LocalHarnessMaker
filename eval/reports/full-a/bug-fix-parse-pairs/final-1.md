Fixed `parse_pairs` without changing its signature or type hints. It now ignores blank lines, splits on the first `=`, strips both sides, preserves empty values, lets the last repeated key win, and rejects invalid records.

Added three regression tests in `test_solution.py`.

Verified: `python -m unittest discover -v` — all 3 tests passed.