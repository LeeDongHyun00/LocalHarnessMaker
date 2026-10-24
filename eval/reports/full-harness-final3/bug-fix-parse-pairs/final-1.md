Fixed `parse_pairs` while preserving its signature and type hints. Added regression tests covering whitespace, blank lines, repeated keys, embedded equals signs, empty values, and invalid records.

Verification passed: compilation and `python -m unittest discover -v` (3 tests).