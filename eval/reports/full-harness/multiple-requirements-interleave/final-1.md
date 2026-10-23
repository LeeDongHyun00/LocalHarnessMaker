Repaired `interleave` to alternate left then right and append the longer input’s remainder in order, without mutating inputs. Preserved type hints and added the public specification docstring.

Added five regression tests covering alternation, unequal lengths, empty inputs, value preservation, and shared inputs.

Verification passed: compilation and `python -m unittest discover -v` (5 tests).