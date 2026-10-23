Implemented `last_index_many` with ordered results, empty-batch support, and unchanged propagation of the first exception. The day-1 API remains unchanged.

Added five batch tests, including input preservation and exception behavior. `python -m unittest discover -v` passed all 11 tests.

Updated `HANDOFF.md` with the verification command and observed result.