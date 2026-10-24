Added `windows_many(cases: list[tuple]) -> list` while preserving the day-1 API. It preserves order and inputs, returns `[]` for empty batches, and propagates the first exception unchanged.

Added five batch tests. `python -m unittest discover -v` passed all 12 tests with exit code 0. Recorded the command and observed result in `HANDOFF.md`.