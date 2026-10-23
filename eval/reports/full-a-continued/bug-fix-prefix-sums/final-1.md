Fixed `prefix` to include the current item in each sum, preserving its signature and leaving inputs unchanged.

Added a regression test covering empty input, a singleton, negative numbers, and input preservation.

`python -m unittest discover -v` passes (1 test).