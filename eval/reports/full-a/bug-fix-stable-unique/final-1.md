Fixed `unique` to preserve first-occurrence order while keeping its signature and leaving input unchanged.

Added regression tests for ordering, case sensitivity, input preservation, and empty input.

Verified: `python -m unittest discover -v` — both tests passed.