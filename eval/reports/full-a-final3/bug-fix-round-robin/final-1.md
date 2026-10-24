Fixed `round_robin` to interleave groups by round, preserving order without modifying inputs or changing its signature.

Added regression tests for uneven groups, empty groups, and input preservation.

Verified: `python -m unittest discover -v` — 2 tests passed.