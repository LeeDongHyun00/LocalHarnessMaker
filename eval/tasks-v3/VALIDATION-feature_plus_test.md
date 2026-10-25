# feature_plus_test offline validation — 2026-10-25

Nine candidates are complete and remain `frozen=false`. This author review does not establish independent acceptance, calibration or host freeze. No model calls were made.

Validation counts are maintained only in [VALIDATION.md](VALIDATION.md).
This file preserves the original shape-session evidence and author pair review.

All nine untouched starters fail substantive checks. Uncovered requirements, unexecuted mutants, shared public assertion lines, shared corpus assertions and corpus warnings: 0 each. Corpus files examined per task: 994. Hash-bound equivalence reviews and requirement derivations are retained outside public inputs.

## Verification

| Check | Passed | Failed |
| --- | ---: | ---: |
| Reference tasks | 9 | 0 |
| Starter rejection | 9 | 0 |
| Requirements | 36 | 0 |
| Public starter smoke tests | 9 | 0 |
| Validator regression tests | 45 | 0 |
| Mutation acceptance | 9 | 0 |

Both validator commands exited 0. `TASK_IDS` expands to exactly the nine IDs in the table; the trusted root is supplied externally. The mutation limit exhausts each declared population.

```sh
.venv/bin/python -m eval.runner.validate_graders --private-root "$LHM_PRIVATE_V3" --tasks $TASK_IDS
.venv/bin/python -m eval.runner.validate_graders --private-root "$LHM_PRIVATE_V3" --tasks $TASK_IDS --mutants 10000
.venv/bin/python -m pytest tests/eval/test_v3_grader_validation.py tests/eval/test_validate_graders.py -q
```

The pytest command reported `45 passed in 39.51s`. Public smoke commands used this worktree’s interpreter with `-B -m unittest discover -s . -p "test_*.py" -v` from each workspace.

## Structure-review pairs

Author pairs: 36. Axes checked: 108. Differing axes: 108. Independent reviewer pairs: 0. The axes are architecture, data flow and failure mechanism; detailed author comparisons remain outside public inputs. Cross-shape independent review remains pending.

| Task | Task | Axes checked | Differing axes |
| --- | --- | ---: | ---: |
| v3-cache-negative | v3-event-watermark | 3 | 3 |
| v3-cache-negative | v3-index-cursor | 3 | 3 |
| v3-cache-negative | v3-link-preview | 3 | 3 |
| v3-cache-negative | v3-plural-catalog | 3 | 3 |
| v3-cache-negative | v3-pool-lease | 3 | 3 |
| v3-cache-negative | v3-scope-explanation | 3 | 3 |
| v3-cache-negative | v3-undo-group | 3 | 3 |
| v3-cache-negative | v3-workflow-checkpoint | 3 | 3 |
| v3-event-watermark | v3-index-cursor | 3 | 3 |
| v3-event-watermark | v3-link-preview | 3 | 3 |
| v3-event-watermark | v3-plural-catalog | 3 | 3 |
| v3-event-watermark | v3-pool-lease | 3 | 3 |
| v3-event-watermark | v3-scope-explanation | 3 | 3 |
| v3-event-watermark | v3-undo-group | 3 | 3 |
| v3-event-watermark | v3-workflow-checkpoint | 3 | 3 |
| v3-index-cursor | v3-link-preview | 3 | 3 |
| v3-index-cursor | v3-plural-catalog | 3 | 3 |
| v3-index-cursor | v3-pool-lease | 3 | 3 |
| v3-index-cursor | v3-scope-explanation | 3 | 3 |
| v3-index-cursor | v3-undo-group | 3 | 3 |
| v3-index-cursor | v3-workflow-checkpoint | 3 | 3 |
| v3-link-preview | v3-plural-catalog | 3 | 3 |
| v3-link-preview | v3-pool-lease | 3 | 3 |
| v3-link-preview | v3-scope-explanation | 3 | 3 |
| v3-link-preview | v3-undo-group | 3 | 3 |
| v3-link-preview | v3-workflow-checkpoint | 3 | 3 |
| v3-plural-catalog | v3-pool-lease | 3 | 3 |
| v3-plural-catalog | v3-scope-explanation | 3 | 3 |
| v3-plural-catalog | v3-undo-group | 3 | 3 |
| v3-plural-catalog | v3-workflow-checkpoint | 3 | 3 |
| v3-pool-lease | v3-scope-explanation | 3 | 3 |
| v3-pool-lease | v3-undo-group | 3 | 3 |
| v3-pool-lease | v3-workflow-checkpoint | 3 | 3 |
| v3-scope-explanation | v3-undo-group | 3 | 3 |
| v3-scope-explanation | v3-workflow-checkpoint | 3 | 3 |
| v3-undo-group | v3-workflow-checkpoint | 3 | 3 |

## Assumptions

- The 60–85% A target remains unmeasured. Offline validation does not establish that target, independent reviewer acceptance or task freeze.
- Consolidation owns shared inventory, configs, estimates and status updates. This session changes only the nine task directories and this validation file.
