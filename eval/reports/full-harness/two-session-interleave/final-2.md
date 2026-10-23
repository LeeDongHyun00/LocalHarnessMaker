Added `interleave_many` with ordered results, empty-batch handling, and unchanged exception propagation. Preserved the existing API and input collections.

Added five batch tests and updated HANDOFF.md with verification evidence.

`python -m unittest discover -v`: all 11 tests passed, exit code 0.