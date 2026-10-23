# Day 2

Complete run_many and render_many using yesterday's naming recipe, domain selection/ordering policy and exact error namespace. Do not replace those decisions with defaults.

D1. Accept only list outer inputs (subclasses allowed), raising TypeError with yesterday's prefix followed by ": batches must be a list" otherwise. run_many returns independent single-input results in encounter order; render_many concatenates the corresponding newline-terminated renders. Empty inputs return [] and "". Apply ALL day-1 policies through the shared compute path exactly once per member, including exact errors and ordering.

D2. Process members in order and fail atomically on the first failing member. Never mutate input on success or failure, and never share nested result state. Preserve yesterday's APIs, protected bytes and dependency restrictions. Extend test_regression.py to exercise both batch APIs, run python verify.py, submit the fresh verification.json and report observed counts and incomplete work. Retain HANDOFF.md.
