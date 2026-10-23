Implemented `normalize_many` with ordered results, empty-batch handling, unchanged exception propagation, and no input mutation. The day-1 API remains unchanged.

Added five batch tests; all 11 tests passed with `python -m unittest discover -v`. Compilation also passed. Updated `HANDOFF.md` with the observed verification results.