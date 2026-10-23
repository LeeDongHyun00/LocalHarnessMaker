Implemented `runs_many` with ordered results, empty-batch support, and unchanged first-exception propagation. Preserved `runs` and input arguments.

Added five batch tests; all 11 tests passed with `python -m unittest discover -v`. Updated `HANDOFF.md` with the command and observed result.