Fixed `round_robin` to interleave groups correctly without modifying inputs or changing its signature or type hints.

Added regression tests for uneven groups, empty groups, and input preservation.

Verified with `python -m unittest discover -v`: **2 tests passed**.