Fixed `unique` to preserve first-occurrence order, case-sensitive equality, and the unchanged typed signature without mutating input.

Added two regression tests covering duplicates, ordering, case, input preservation, and empty input.

Validation: `python -m unittest discover -v` passed both tests; compilation passed.