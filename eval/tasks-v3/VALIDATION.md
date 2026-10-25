# Version 3 offline validation — 2026-10-25

Canonical validation counts for all 54 candidates (six shapes, nine each).
All metadata remains `frozen=false`; all run templates are `draft_not_approved`.
These are consolidated author-session results, not private-grader reruns in
this session. References pass and untouched starters fail for all 54 tasks.
Independent Claude host review, disjoint calibration and task freeze remain
pending. No measured model quality or H3 compatibility is claimed.

## bug_fix

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

## feature_plus_test

| Task ID | Requirements covered | Reference pass | Starter fail | Generated | Targeted | Executed | Killed | Equivalent | Survivors | Errors |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| v3-cache-negative | 4 | 6 | 4 | 32 | 2 | 34 | 30 | 4 | 0 | 0 |
| v3-event-watermark | 4 | 5 | 4 | 42 | 2 | 44 | 41 | 3 | 0 | 0 |
| v3-index-cursor | 4 | 5 | 4 | 92 | 2 | 94 | 86 | 8 | 0 | 0 |
| v3-link-preview | 4 | 6 | 5 | 8 | 2 | 10 | 9 | 1 | 0 | 0 |
| v3-plural-catalog | 4 | 5 | 3 | 39 | 2 | 41 | 39 | 2 | 0 | 0 |
| v3-pool-lease | 4 | 6 | 3 | 59 | 2 | 61 | 54 | 7 | 0 | 0 |
| v3-scope-explanation | 4 | 6 | 5 | 41 | 2 | 43 | 40 | 3 | 0 | 0 |
| v3-undo-group | 4 | 6 | 5 | 14 | 2 | 16 | 15 | 1 | 0 | 0 |
| v3-workflow-checkpoint | 4 | 6 | 4 | 57 | 2 | 59 | 55 | 4 | 0 | 0 |
| Total | 36 | 51 | 37 | 384 | 18 | 402 | 369 | 33 | 0 | 0 |

## constrained_refactoring

| Task ID | Requirements covered | Reference pass | Starter fail | Generated | Targeted | Executed | Killed | Equivalent | Survivors | Errors |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| v3-build-manifest | 4 | 6 | 5 | 14 | 2 | 16 | 16 | 0 | 0 | 0 |
| v3-config-dispatch | 4 | 6 | 4 | 63 | 2 | 65 | 62 | 3 | 0 | 0 |
| v3-fixedwidth-plan | 4 | 6 | 2 | 36 | 2 | 38 | 37 | 1 | 0 | 0 |
| v3-html-events | 4 | 5 | 1 | 15 | 2 | 17 | 16 | 1 | 0 | 0 |
| v3-journal-codec | 4 | 7 | 4 | 70 | 2 | 72 | 68 | 4 | 0 | 0 |
| v3-log-sink | 4 | 7 | 3 | 29 | 2 | 31 | 28 | 3 | 0 | 0 |
| v3-path-reconstruction | 4 | 5 | 1 | 17 | 2 | 19 | 19 | 0 | 0 | 0 |
| v3-ready-queue | 4 | 5 | 1 | 23 | 2 | 25 | 21 | 4 | 0 | 0 |
| v3-token-scanner | 4 | 7 | 2 | 89 | 3 | 92 | 86 | 6 | 0 | 0 |
| Total | 36 | 54 | 23 | 356 | 19 | 375 | 353 | 22 | 0 | 0 |

## multiple_requirements

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

## two_session

| Task ID | Requirements covered | Reference pass | Starter fail | Generated | Targeted | Executed | Killed | Equivalent | Survivors | Errors |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| v3-component-order | 5 | 5 | 4 | 66 | 2 | 68 | 65 | 3 | 0 | 0 |
| v3-document-theme | 5 | 5 | 4 | 44 | 2 | 46 | 46 | 0 | 0 | 0 |
| v3-import-reconcile | 5 | 5 | 5 | 58 | 2 | 60 | 57 | 3 | 0 | 0 |
| v3-package-lock | 5 | 6 | 5 | 105 | 2 | 107 | 100 | 7 | 0 | 0 |
| v3-page-recovery | 5 | 8 | 8 | 66 | 2 | 68 | 66 | 2 | 0 | 0 |
| v3-secret-redaction | 5 | 5 | 5 | 75 | 2 | 77 | 70 | 7 | 0 | 0 |
| v3-shift-calendar | 5 | 6 | 5 | 94 | 2 | 96 | 93 | 3 | 0 | 0 |
| v3-stream-negotiation | 5 | 6 | 6 | 71 | 2 | 73 | 70 | 3 | 0 | 0 |
| v3-trace-sampling | 5 | 6 | 6 | 113 | 2 | 115 | 104 | 11 | 0 | 0 |
| Total | 45 | 52 | 48 | 692 | 18 | 710 | 671 | 39 | 0 | 0 |

## ambiguous_requirement

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

## Population totals

| Scope | Requirements covered | Reference pass | Starter fail | Generated | Targeted | Executed | Killed | Equivalent | Survivors | Errors |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| All 54 | 225 | 325 | 253 | 3057 | 111 | 3168 | 2980 | 188 | 0 | 0 |

All recorded mutation populations were exhausted; survivors, errors and
unexecuted mutants are zero. Equivalence rationales remain private and hash-bound;
timeouts are unresolved, never kills. Recorded uncovered requirements, public
assertion overlap, corpus assertion overlap and corpus warnings are zero.
Each shape recorded nine passing public starter smoke checks. Corpus scans used
994 distinct retained files; these counts concern author validation, not the
new sanitized command-stream regression fixtures.

The ambiguity session records nine matchers, 19 positive, 63 negative and 19
normalization fixtures. Two-session tasks retain day-2 prompts and private
carryover checks. Per-shape files preserve original command evidence and author
pair reviews; this file is the sole source of task validation counts.
[STRUCTURE-REVIEW.md](STRUCTURE-REVIEW.md) adds cross-shape author comparisons;
independent all-population review remains required.

Reproduction on the trusted host only: expand TASK_IDS to all IDs above. The
private root is supplied externally; it is unavailable in this session.

```sh
.venv/bin/python -m eval.runner.validate_graders --private-root "$LHM_PRIVATE_V3" --tasks TASK_IDS
.venv/bin/python -m eval.runner.validate_graders --private-root "$LHM_PRIVATE_V3" --tasks TASK_IDS --mutants 10000
```

Original shape sessions record exit 0 for both commands and 45 passing validator
regression tests each. Bug-fix history records 2,123 eval tests passing in 467.32s,
then 45 validator tests in 16.58s. This consolidation does not renew private
hash bindings or constitute independent host acceptance.
