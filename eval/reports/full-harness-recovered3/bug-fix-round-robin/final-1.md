Fixed `round_robin` to interleave groups in order without mutating inputs, preserving its signature and type hints.

Added two regression tests covering uneven groups, empty groups, and input preservation.

Compilation and `python -m unittest discover -v` passed.