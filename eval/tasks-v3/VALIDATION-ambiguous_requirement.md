# Version 3 ambiguous_requirement validation — 2026-10-25

Authored: 9/9. Frozen: 0/9. Model calls: 0. Measured A pass rate: unavailable;
60–85% remains an unmeasured target. Independent reviewer acceptance: 0.
Both validator commands exited 0. Canonical counts linked below are the original offline results.

Validation counts are maintained only in [VALIDATION.md](VALIDATION.md).
This file preserves the original shape-session evidence and author pair review.

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
