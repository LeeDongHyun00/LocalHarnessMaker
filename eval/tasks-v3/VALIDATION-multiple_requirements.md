# Version 3 multiple_requirements offline validation — 2026-10-25

Nine `multiple_requirements` candidates are authored and offline-validated. All
remain `frozen=false`. Live calibration, measured A pass rate, independent host
reviewer acceptance and population freeze remain pending. Paid calls: 0.

| Task ID | Requirements covered | Reference pass | Starter fail | Generated | Targeted | Executed | Killed | Equivalent | Survivors | Errors |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| v3-archive-extract | 5 | 10 | 9 | 99 | 2 | 101 | 97 | 4 | 0 | 0 |
| v3-cache-invalidation | 5 | 8 | 8 | 99 | 2 | 101 | 95 | 6 | 0 | 0 |
| v3-catalog-extract | 5 | 6 | 6 | 62 | 2 | 64 | 61 | 3 | 0 | 0 |
| v3-connection-drain | 6 | 8 | 8 | 97 | 2 | 99 | 80 | 19 | 0 | 0 |
| v3-job-compensation | 5 | 10 | 10 | 58 | 2 | 60 | 57 | 3 | 0 | 0 |
| v3-policy-migration | 5 | 6 | 6 | 52 | 2 | 54 | 52 | 2 | 0 | 0 |
| v3-query-explain | 5 | 6 | 6 | 202 | 2 | 204 | 188 | 16 | 0 | 0 |
| v3-replay-dedup | 5 | 8 | 8 | 103 | 2 | 105 | 101 | 4 | 0 | 0 |
| v3-selection-patch | 5 | 8 | 8 | 99 | 2 | 101 | 94 | 7 | 0 | 0 |
| Total | 46 | 70 | 69 | 871 | 18 | 889 | 825 | 64 | 0 | 0 |

All 9 starters fail substantive checks. Uncovered requirements: 0. Unexecuted
mutants, unresolved errors, survivors and shared assertion lines across public
task versions: 0 each. Corpus files examined per task: 994; 8,946 task/file
comparisons. Shared corpus assertion lines and corpus warnings: 0. Equivalent
cases have individual source/specification hash-bound semantic reviews retained
privately. Timeouts are unresolved; none remains in the final population.

The following author comparison covers 36 pairs on architecture, data flow and
failure mechanism. Detailed rationales remain private. Independent host-review
pairs: 0; this author review does not replace that acceptance gate.

| Task | Task | Axes checked | Differing axes |
| --- | --- | ---: | ---: |
| v3-archive-extract | v3-cache-invalidation | 3 | 3 |
| v3-archive-extract | v3-catalog-extract | 3 | 3 |
| v3-archive-extract | v3-connection-drain | 3 | 3 |
| v3-archive-extract | v3-job-compensation | 3 | 3 |
| v3-archive-extract | v3-policy-migration | 3 | 3 |
| v3-archive-extract | v3-query-explain | 3 | 3 |
| v3-archive-extract | v3-replay-dedup | 3 | 3 |
| v3-archive-extract | v3-selection-patch | 3 | 3 |
| v3-cache-invalidation | v3-catalog-extract | 3 | 3 |
| v3-cache-invalidation | v3-connection-drain | 3 | 3 |
| v3-cache-invalidation | v3-job-compensation | 3 | 3 |
| v3-cache-invalidation | v3-policy-migration | 3 | 3 |
| v3-cache-invalidation | v3-query-explain | 3 | 3 |
| v3-cache-invalidation | v3-replay-dedup | 3 | 3 |
| v3-cache-invalidation | v3-selection-patch | 3 | 3 |
| v3-catalog-extract | v3-connection-drain | 3 | 3 |
| v3-catalog-extract | v3-job-compensation | 3 | 3 |
| v3-catalog-extract | v3-policy-migration | 3 | 3 |
| v3-catalog-extract | v3-query-explain | 3 | 3 |
| v3-catalog-extract | v3-replay-dedup | 3 | 3 |
| v3-catalog-extract | v3-selection-patch | 3 | 3 |
| v3-connection-drain | v3-job-compensation | 3 | 3 |
| v3-connection-drain | v3-policy-migration | 3 | 3 |
| v3-connection-drain | v3-query-explain | 3 | 3 |
| v3-connection-drain | v3-replay-dedup | 3 | 3 |
| v3-connection-drain | v3-selection-patch | 3 | 3 |
| v3-job-compensation | v3-policy-migration | 3 | 3 |
| v3-job-compensation | v3-query-explain | 3 | 3 |
| v3-job-compensation | v3-replay-dedup | 3 | 3 |
| v3-job-compensation | v3-selection-patch | 3 | 3 |
| v3-policy-migration | v3-query-explain | 3 | 3 |
| v3-policy-migration | v3-replay-dedup | 3 | 3 |
| v3-policy-migration | v3-selection-patch | 3 | 3 |
| v3-query-explain | v3-replay-dedup | 3 | 3 |
| v3-query-explain | v3-selection-patch | 3 | 3 |
| v3-replay-dedup | v3-selection-patch | 3 | 3 |

Reproduce with the trusted root supplied externally as `LHM_PRIVATE_V3`:

```sh
TASK_IDS=(v3-archive-extract v3-cache-invalidation v3-catalog-extract v3-connection-drain v3-job-compensation v3-policy-migration v3-query-explain v3-replay-dedup v3-selection-patch)
.venv/bin/python -m eval.runner.validate_graders --private-root "$LHM_PRIVATE_V3" --tasks "${TASK_IDS[@]}"
.venv/bin/python -m eval.runner.validate_graders --private-root "$LHM_PRIVATE_V3" --tasks "${TASK_IDS[@]}" --mutants 10000
.venv/bin/python -m pytest tests/eval/test_v3_grader_validation.py tests/eval/test_validate_graders.py -q
```

Both validator commands exited 0. The mutation limit exhausts every declared
population. The requested regression tests passed: 45 in 30.48 seconds.

Public starter smoke tests: 9/9 passed using this worktree's interpreter with
`-m unittest discover -s . -p "test_*.py" -v`, separately from each workspace.

## Assumptions

- The 60–85% A target is unmeasured. No A/H3 outcomes were used for selection or tuning.
- These 9 single-session candidates require 9 executor sessions per configuration; calibration, independent review and freeze belong to consolidation.
- Shared status, configs, estimates and cross-shape review files remain for the consolidation session.
