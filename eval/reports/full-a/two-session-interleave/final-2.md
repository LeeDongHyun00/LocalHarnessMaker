Added `interleave_many` with ordered results, empty-batch support, and unchanged propagation of the first exception. The day-1 API remains unchanged; cases and arguments are preserved.

`python -m unittest discover -v` passed all 11 tests. Updated `HANDOFF.md` with the command and observed result.