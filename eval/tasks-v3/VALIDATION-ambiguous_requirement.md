# Version 3 ambiguous_requirement validation — 2026-10-25

Authored: 9/9. Frozen: 0/9. Model calls: 0. Measured A pass rate: unavailable;
60–85% remains an unmeasured target. Independent reviewer acceptance: 0.
Both validator commands exited 0. Counts below are final offline results.

| Task ID | Requirements covered | Reference pass | Starter fail | Generated | Targeted | Executed | Killed | Equivalent | Survivors | Errors |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| v3-approval-quorum | 3 | 5 | 3 | 41 | 2 | 43 | 42 | 1 | 0 | 0 |
| v3-cache-refresh | 4 | 6 | 5 | 41 | 2 | 43 | 40 | 3 | 0 | 0 |
| v3-copy-collision | 4 | 6 | 8 | 16 | 4 | 20 | 19 | 1 | 0 | 0 |
| v3-editor-anchor | 4 | 5 | 14 | 80 | 2 | 82 | 77 | 5 | 0 | 0 |
| v3-event-tie | 4 | 5 | 5 | 55 | 2 | 57 | 55 | 2 | 0 | 0 |
| v3-locale-fallback | 3 | 5 | 5 | 13 | 2 | 15 | 15 | 0 | 0 | 0 |
| v3-pool-resize | 3 | 5 | 5 | 38 | 2 | 40 | 40 | 0 | 0 | 0 |
| v3-search-empty | 4 | 6 | 6 | 61 | 2 | 63 | 62 | 1 | 0 | 0 |
| v3-token-expiry | 3 | 5 | 4 | 59 | 2 | 61 | 60 | 1 | 0 | 0 |
| Total | 32 | 48 | 55 | 404 | 20 | 424 | 410 | 14 | 0 | 0 |

Starter failure counts include failed subtests. Public starter smoke checks: 9/9.
Uncovered requirements, unexecuted mutants, shared public assertion lines,
shared corpus assertion lines and corpus warnings: 0 each. Distinct retained
corpus files examined per task: 994. Equivalent reviews are hash-bound and
retained privately; unresolved/time-out mutations: 0.

Question matchers: 9; positive fixtures: 19; unrelated/negative fixtures: 63;
normalization fixtures: 19. Author structure pairs: 36 × 3 axes; independent
review pairs: 0. Calibration, host review and task freeze remain pending.

Validator limitations blocking authoring: 0. No shared tooling was changed.

Reproduce using the nine task IDs above as TASK_IDS and the trusted root
supplied externally as LHM_PRIVATE_V3:

```sh
.venv/bin/python -m eval.runner.validate_graders --private-root "$LHM_PRIVATE_V3" --tasks TASK_IDS
.venv/bin/python -m eval.runner.validate_graders --private-root "$LHM_PRIVATE_V3" --tasks TASK_IDS --mutants 10000
.venv/bin/python -m pytest tests/eval/test_v3_grader_validation.py tests/eval/test_validate_graders.py -q
```

Regression tests: 45 passed in 31.90s; exit 0. Exhaustive mutation counts
include the full generated population and every declared targeted mutant.

| Task | Task | Axes checked | Differing axes |
| --- | --- | ---: | ---: |
| v3-approval-quorum | v3-cache-refresh | 3 | 3 |
| v3-approval-quorum | v3-copy-collision | 3 | 3 |
| v3-approval-quorum | v3-editor-anchor | 3 | 3 |
| v3-approval-quorum | v3-event-tie | 3 | 3 |
| v3-approval-quorum | v3-locale-fallback | 3 | 3 |
| v3-approval-quorum | v3-pool-resize | 3 | 3 |
| v3-approval-quorum | v3-search-empty | 3 | 3 |
| v3-approval-quorum | v3-token-expiry | 3 | 3 |
| v3-cache-refresh | v3-copy-collision | 3 | 3 |
| v3-cache-refresh | v3-editor-anchor | 3 | 3 |
| v3-cache-refresh | v3-event-tie | 3 | 3 |
| v3-cache-refresh | v3-locale-fallback | 3 | 3 |
| v3-cache-refresh | v3-pool-resize | 3 | 3 |
| v3-cache-refresh | v3-search-empty | 3 | 3 |
| v3-cache-refresh | v3-token-expiry | 3 | 3 |
| v3-copy-collision | v3-editor-anchor | 3 | 3 |
| v3-copy-collision | v3-event-tie | 3 | 3 |
| v3-copy-collision | v3-locale-fallback | 3 | 3 |
| v3-copy-collision | v3-pool-resize | 3 | 3 |
| v3-copy-collision | v3-search-empty | 3 | 3 |
| v3-copy-collision | v3-token-expiry | 3 | 3 |
| v3-editor-anchor | v3-event-tie | 3 | 3 |
| v3-editor-anchor | v3-locale-fallback | 3 | 3 |
| v3-editor-anchor | v3-pool-resize | 3 | 3 |
| v3-editor-anchor | v3-search-empty | 3 | 3 |
| v3-editor-anchor | v3-token-expiry | 3 | 3 |
| v3-event-tie | v3-locale-fallback | 3 | 3 |
| v3-event-tie | v3-pool-resize | 3 | 3 |
| v3-event-tie | v3-search-empty | 3 | 3 |
| v3-event-tie | v3-token-expiry | 3 | 3 |
| v3-locale-fallback | v3-pool-resize | 3 | 3 |
| v3-locale-fallback | v3-search-empty | 3 | 3 |
| v3-locale-fallback | v3-token-expiry | 3 | 3 |
| v3-pool-resize | v3-search-empty | 3 | 3 |
| v3-pool-resize | v3-token-expiry | 3 | 3 |
| v3-search-empty | v3-token-expiry | 3 | 3 |

Assumptions: no model outcomes inform these candidates; calibration and independent
review have not occurred. Single-session tasks: 9; two-session tasks: 0.
