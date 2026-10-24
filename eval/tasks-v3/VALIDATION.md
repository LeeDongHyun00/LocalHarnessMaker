# Version 3 offline validation — 2026-10-25

The complete `bug_fix` shape is authored and offline-validated: 9 of 54 tasks,
1 of 6 shapes. Every candidate remains `frozen=false`; both configs remain
`draft_not_approved`. Other shapes have 0 authored tasks. No live calibration,
measured A pass rate, independent reviewer acceptance or host freeze is claimed.

| Task ID | Requirements covered | Reference pass | Starter fail | Generated | Targeted | Executed | Killed | Equivalent | Survivors | Errors |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| v3-cancelled-deadline | 4 | 5 | 1 | 28 | 2 | 30 | 28 | 2 | 0 | 0 |
| v3-cycle-witness | 3 | 5 | 2 | 28 | 2 | 30 | 29 | 1 | 0 | 0 |
| v3-framed-stream | 4 | 6 | 5 | 15 | 2 | 17 | 16 | 1 | 0 | 0 |
| v3-histogram-merge | 3 | 6 | 2 | 30 | 2 | 32 | 32 | 0 | 0 | 0 |
| v3-incremental-fanout | 3 | 6 | 2 | 60 | 2 | 62 | 60 | 2 | 0 | 0 |
| v3-origin-shadow | 3 | 5 | 2 | 35 | 2 | 37 | 37 | 0 | 0 | 0 |
| v3-quoted-record | 4 | 6 | 2 | 81 | 2 | 83 | 77 | 6 | 0 | 0 |
| v3-savepoint-unwind | 3 | 5 | 3 | 17 | 2 | 19 | 16 | 3 | 0 | 0 |
| v3-wide-column | 3 | 6 | 2 | 56 | 2 | 58 | 57 | 1 | 0 | 0 |
| Total | 30 | 50 | 21 | 350 | 18 | 368 | 352 | 16 | 0 | 0 |

All nine starters fail at least one substantive check. Uncovered requirements,
unexecuted mutants and shared assertion lines across all public task versions:
0 each. The retained executor corpus contains 2,754 examined file occurrences,
994 distinct files; shared corpus assertion lines and warnings: 0. Equivalence
rationales and hashes are retained privately; no survivor was automatically waived.
Timeouts are unresolved, never kills, under v3 validation.

The [structure table](STRUCTURE-REVIEW.md) records 36 author-reviewed pairs on
three axes; independent host-review pairs: 0. That independent review, ten
disjoint calibration tasks, the approved A-only pilot, remaining 45 tasks and
all-population host validation/freeze remain pending. No task was selected or
changed using A/H3 outcomes.

Reproduce with the trusted root supplied externally as `LHM_PRIVATE_V3` and
`TASK_IDS` expanded to the nine IDs in the table:

```sh
.venv/bin/python -m eval.runner.validate_graders --private-root "$LHM_PRIVATE_V3" --tasks TASK_IDS
.venv/bin/python -m eval.runner.validate_graders --private-root "$LHM_PRIVATE_V3" --tasks TASK_IDS --mutants 10000
```

Both commands exited 0. The mutation limit exceeds the entire declared population;
there is no sampled or timed-out remainder. These are offline tool checks, with
no executor model or control call.

Package verification: `.venv/bin/python -m pytest tests/eval -q` — 2,123 passed
in 467.32s. The final validator-only follow-up ran 45 tests in 16.58s, including
three cases added after full-run collection, with this exact command:

```sh
.venv/bin/python -m pytest tests/eval/test_v3_grader_validation.py tests/eval/test_validate_graders.py -q
```

Public starter smoke tests: 9 passed. Scope and marker scans: 0 private-path
matches, 0 private-marker matches, 0 staged paths and 0 deleted paths.
