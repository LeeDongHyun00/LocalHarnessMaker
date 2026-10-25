# Version 3 two-session offline validation — 2026-10-25

Nine two-session candidates, 18 required executor sessions; 9 remain unfrozen. All day-2 requests depend on at least three day-1 policy decisions. Calibration, the 60–85% A target, independent review and host freeze remain unmeasured/pending. No paid calls or model outcomes were used.

Validation counts are maintained only in [VALIDATION.md](VALIDATION.md).
This file preserves the original shape-session evidence and author pair review.

Uncovered requirements, shared public assertion lines, shared corpus assertion lines, corpus warnings, unresolved mutants and unexecuted mutants: 0 each. The corpus scan examined 994 distinct retained files per task (8,946 task/file occurrences). All generated and targeted populations were exhausted; equivalence reviews are private and hash-bound. Timeouts are unresolved, never counted as kills.

Public starter smoke checks: 9 passed. Validator regression checks: 45 passed. Final scope check: 0 foreign repository paths, 0 staged/deleted paths and 0 private-path matches. No validator limitation remains blocking. Full repository tests remain a pre-merge consolidation gate.

Reproduction (supply the trusted root externally; TASK_IDS is the nine IDs above):

```sh
.venv/bin/python -m eval.runner.validate_graders --private-root "$LHM_PRIVATE_V3" --tasks TASK_IDS
.venv/bin/python -m eval.runner.validate_graders --private-root "$LHM_PRIVATE_V3" --tasks TASK_IDS --mutants 10000
.venv/bin/python -m eval.runner.validate_graders --private-root "$LHM_PRIVATE_V3" --tasks v3-component-order v3-shift-calendar --mutants 10000
.venv/bin/python -m pytest tests/eval/test_v3_grader_validation.py tests/eval/test_validate_graders.py -q
git diff --check
```

The all-nine validation and mutation commands exit 0. The final two-task mutation follow-up binds the revised work-budget and finite-enumeration checks. No shared interfaces, runners, configs, historical inputs or consolidation files were edited.

## Structure comparison

Author review: 36 pairs, three axes per pair (architecture, data flow, failure mechanism). The tree-based rendering/redaction pair shares traversal mechanics while differing in data flow and failure mechanism. Independent review pairs: 0; cross-shape/all-population review remains pending. Private rationales retain the pair comparisons and carryover maps.

| Task | Task | Axes checked | Differing axes |
| --- | --- | ---: | ---: |
| v3-component-order | v3-document-theme | 3 | 3 |
| v3-component-order | v3-import-reconcile | 3 | 3 |
| v3-component-order | v3-package-lock | 3 | 3 |
| v3-component-order | v3-page-recovery | 3 | 3 |
| v3-component-order | v3-secret-redaction | 3 | 3 |
| v3-component-order | v3-shift-calendar | 3 | 3 |
| v3-component-order | v3-stream-negotiation | 3 | 3 |
| v3-component-order | v3-trace-sampling | 3 | 3 |
| v3-document-theme | v3-import-reconcile | 3 | 3 |
| v3-document-theme | v3-package-lock | 3 | 3 |
| v3-document-theme | v3-page-recovery | 3 | 3 |
| v3-document-theme | v3-secret-redaction | 3 | 2 |
| v3-document-theme | v3-shift-calendar | 3 | 3 |
| v3-document-theme | v3-stream-negotiation | 3 | 3 |
| v3-document-theme | v3-trace-sampling | 3 | 3 |
| v3-import-reconcile | v3-package-lock | 3 | 3 |
| v3-import-reconcile | v3-page-recovery | 3 | 3 |
| v3-import-reconcile | v3-secret-redaction | 3 | 3 |
| v3-import-reconcile | v3-shift-calendar | 3 | 3 |
| v3-import-reconcile | v3-stream-negotiation | 3 | 3 |
| v3-import-reconcile | v3-trace-sampling | 3 | 3 |
| v3-package-lock | v3-page-recovery | 3 | 3 |
| v3-package-lock | v3-secret-redaction | 3 | 3 |
| v3-package-lock | v3-shift-calendar | 3 | 3 |
| v3-package-lock | v3-stream-negotiation | 3 | 3 |
| v3-package-lock | v3-trace-sampling | 3 | 3 |
| v3-page-recovery | v3-secret-redaction | 3 | 3 |
| v3-page-recovery | v3-shift-calendar | 3 | 3 |
| v3-page-recovery | v3-stream-negotiation | 3 | 3 |
| v3-page-recovery | v3-trace-sampling | 3 | 3 |
| v3-secret-redaction | v3-shift-calendar | 3 | 3 |
| v3-secret-redaction | v3-stream-negotiation | 3 | 3 |
| v3-secret-redaction | v3-trace-sampling | 3 | 3 |
| v3-shift-calendar | v3-stream-negotiation | 3 | 3 |
| v3-shift-calendar | v3-trace-sampling | 3 | 3 |
| v3-stream-negotiation | v3-trace-sampling | 3 | 3 |

## Assumptions

- Candidates remain unfrozen; offline acceptance does not measure model pass rate or satisfy independent review.
- Ordinary retained workspace files are available on day 2; no synthesized baseline memory or day-1 prompt is injected.
- The consolidation session owns shared validation, configs, estimates, CHANGES and STATUS updates.
