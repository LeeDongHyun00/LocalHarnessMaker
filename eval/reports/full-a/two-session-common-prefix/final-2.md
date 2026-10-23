Added `common_many` with ordered results, empty-batch handling, unchanged exception propagation, and no input mutation. The day-1 API remains unchanged.

Verification: `python -m unittest discover -v` — all 12 tests passed. `HANDOFF.md` records the command and observed result.