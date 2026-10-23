Added `invert_many(cases: list[tuple]) -> list` with ordered results, empty-batch support, unchanged exception propagation, and no input mutation. The Day 1 API remains compatible.

All 10 tests passed with `python -m unittest discover -v`. `HANDOFF.md` records the command and observed result.