Implemented `unique_many` with ordered results, empty-batch handling, unchanged inputs, and immediate propagation of the first exception. The day-1 API remains unchanged.

Verification: `python -m unittest discover -v` passed all 11 tests, including five batch tests. Recorded the command and observed result in `HANDOFF.md`.