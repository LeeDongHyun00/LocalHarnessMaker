Implemented `merge_many` with ordered results, empty-batch support, unchanged inputs, and first-exception propagation. The Day 1 API remains unchanged.

Verification: `python -m unittest discover -v` — all 10 tests passed.

Updated `HANDOFF.md` with the command and observed result.