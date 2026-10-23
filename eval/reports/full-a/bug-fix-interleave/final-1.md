Fixed `interleave` to alternate left then right and append remaining items in order, preserving its signature, type hints, and inputs.

Added regression coverage for equal and unequal lengths, empty inputs, and input preservation.

`python -m unittest discover -v` passed: 1 test.