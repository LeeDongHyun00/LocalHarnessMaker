# Version 3 constrained_refactoring validation — 2026-10-25

Nine candidates, all `frozen=false`. Offline author validation only. Independent
review, host acceptance, calibration and freeze remain pending. The 60–85% A
pass-rate target is unmeasured; no model calls or outcome-based selection occurred.

Both validation commands exited 0. All references pass, all untouched starters
fail at least one substantive requirement, and all 36 requirements have executed
coverage. The declared mutation population is exhausted. Equivalence reviews are
hash-bound and retained privately; no survivor was automatically waived.

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

Uncovered requirements, unexecuted mutants, shared public assertion lines and
corpus warnings: 0 each. Corpus files: 994 distinct files, 8,946 examined
occurrences across nine checks. No timeout is counted as a kill. Public starter
smoke tests: 9 passed. Validator limitations blocking acceptance: 0.

Author structure comparison checks architecture, data flow and failure mechanism.
The detailed author rationale remains outside public inputs. These comparisons
are construction checks; independent reviewer acceptance is pending.

| Task | Task | Axes checked | Differing axes |
| --- | --- | ---: | ---: |
| v3-build-manifest | v3-config-dispatch | 3 | 3 |
| v3-build-manifest | v3-fixedwidth-plan | 3 | 2 |
| v3-build-manifest | v3-html-events | 3 | 3 |
| v3-build-manifest | v3-journal-codec | 3 | 3 |
| v3-build-manifest | v3-log-sink | 3 | 3 |
| v3-build-manifest | v3-path-reconstruction | 3 | 3 |
| v3-build-manifest | v3-ready-queue | 3 | 3 |
| v3-build-manifest | v3-token-scanner | 3 | 3 |
| v3-config-dispatch | v3-fixedwidth-plan | 3 | 3 |
| v3-config-dispatch | v3-html-events | 3 | 3 |
| v3-config-dispatch | v3-journal-codec | 3 | 3 |
| v3-config-dispatch | v3-log-sink | 3 | 3 |
| v3-config-dispatch | v3-path-reconstruction | 3 | 3 |
| v3-config-dispatch | v3-ready-queue | 3 | 3 |
| v3-config-dispatch | v3-token-scanner | 3 | 3 |
| v3-fixedwidth-plan | v3-html-events | 3 | 3 |
| v3-fixedwidth-plan | v3-journal-codec | 3 | 3 |
| v3-fixedwidth-plan | v3-log-sink | 3 | 3 |
| v3-fixedwidth-plan | v3-path-reconstruction | 3 | 3 |
| v3-fixedwidth-plan | v3-ready-queue | 3 | 3 |
| v3-fixedwidth-plan | v3-token-scanner | 3 | 3 |
| v3-html-events | v3-journal-codec | 3 | 3 |
| v3-html-events | v3-log-sink | 3 | 3 |
| v3-html-events | v3-path-reconstruction | 3 | 3 |
| v3-html-events | v3-ready-queue | 3 | 3 |
| v3-html-events | v3-token-scanner | 3 | 3 |
| v3-journal-codec | v3-log-sink | 3 | 2 |
| v3-journal-codec | v3-path-reconstruction | 3 | 3 |
| v3-journal-codec | v3-ready-queue | 3 | 3 |
| v3-journal-codec | v3-token-scanner | 3 | 3 |
| v3-log-sink | v3-path-reconstruction | 3 | 3 |
| v3-log-sink | v3-ready-queue | 3 | 3 |
| v3-log-sink | v3-token-scanner | 3 | 3 |
| v3-path-reconstruction | v3-ready-queue | 3 | 3 |
| v3-path-reconstruction | v3-token-scanner | 3 | 3 |
| v3-ready-queue | v3-token-scanner | 3 | 3 |

Same-domain comparisons with the completed bug_fix shape:

| Task | Task | Axes checked | Differing axes |
| --- | --- | ---: | ---: |
| v3-token-scanner | v3-framed-stream | 3 | 3 |
| v3-journal-codec | v3-savepoint-unwind | 3 | 3 |
| v3-ready-queue | v3-cancelled-deadline | 3 | 2 |
| v3-html-events | v3-wide-column | 3 | 3 |
| v3-fixedwidth-plan | v3-quoted-record | 3 | 3 |
| v3-path-reconstruction | v3-cycle-witness | 3 | 2 |
| v3-config-dispatch | v3-origin-shadow | 3 | 3 |
| v3-build-manifest | v3-incremental-fanout | 3 | 3 |
| v3-log-sink | v3-histogram-merge | 3 | 3 |

Author-reviewed pairs: 45; axes checked: 135; independent-review pairs: 0.
Other shapes and the complete 54-task independent review remain pending.

Reproduce the two offline validation modes with the externally supplied trusted
root and the nine task IDs above. No private location or content is published.

```sh
.venv/bin/python -m eval.runner.validate_graders --private-root "$LHM_PRIVATE_V3" --tasks TASK_IDS
.venv/bin/python -m eval.runner.validate_graders --private-root "$LHM_PRIVATE_V3" --tasks TASK_IDS --mutants 10000
.venv/bin/python -m pytest tests/eval/test_v3_grader_validation.py tests/eval/test_validate_graders.py -q
```

Regression tests: 45 passed in 30.81 seconds. Public starter smoke tests: 9 passed.
Scope/marker/whitespace audit: 47 new repository files, 0 out-of-scope paths,
0 private markers, 0 staged paths, 0 deleted paths and 0 whitespace errors.
The full repository suite remains a pre-merge host check; no merge is performed.
No runner, schema, CLI, configuration or historical task change is included.

## Assumptions

- Candidate authoring does not establish calibration, independent acceptance,
  host compatibility or a frozen population.
- This session's consolidation handoff is this file; the shared STATUS and
  population inventory remain owned by the consolidation session.
