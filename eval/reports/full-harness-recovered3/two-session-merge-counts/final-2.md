Added `merge_many` with ordered results, empty-batch handling, unchanged exception propagation, and no input mutation. The existing `merge` API is unchanged.

All 8 tests passed with `python -m unittest discover -v` (exit 0). Updated `HANDOFF.md` with the command and observed result.