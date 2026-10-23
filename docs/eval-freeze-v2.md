# Evaluation task set version 2 freeze (D-3)

Frozen on 2026-10-24 and merged into main as commit `9097281`. Every task
`meta.json` declares `frozen=true`. Claude verified the facts below on the
host on 2026-10-24 at that commit; the user supplied those findings for this
record. This documentation session did not rerun evaluation or private grading.

Task-set SHA-256:

```text
12e7574905a6c6e4f7f49a85eacad38899fa5f0d221a3c93939a83ab13b6f041
```

The digest was computed with `eval.freeze_v2` over public inputs plus external
grader contents. Private grader locations and contents are not published here.

## Scope and inventory

Version 2 contains 100 tasks in `eval/tasks-v2/`: 20 families of 5 tasks,
including 80 single-session and 20 two-session tasks. Two-session tasks are
included in the multiple-requirements count below, not additional tasks.

| Type | Tasks | Two-session tasks included |
|---|---:|---:|
| `bug_fix` | 20 | 0 |
| `feature_plus_test` | 20 | 0 |
| `constrained_refactoring` | 20 | 0 |
| `multiple_requirements` | 40 | 20 |
| Total | 100 | 20 |

| Family | Tasks |
|---|---:|
| access-policy | 5 |
| cache-invalidation | 5 |
| calendar-windows | 5 |
| command-dispatch | 5 |
| csv-import | 5 |
| dependency-graph | 5 |
| document-patches | 5 |
| event-replay | 5 |
| filesystem-manifests | 5 |
| inventory | 5 |
| job-queues | 5 |
| layered-settings | 5 |
| ledger | 5 |
| rate-budgets | 5 |
| reservations | 5 |
| routing | 5 |
| schema-migration | 5 |
| search-facets | 5 |
| text-indexing | 5 |
| workflow-state | 5 |

## Host verification evidence

Claude's host verification at `9097281` confirmed the following Role 5
validation results and independent checks. No exact host command invocation
was supplied beyond the digest module name; none is inferred here.

| Check | Result |
|---|---|
| Role 5 reference validation | 100 references pass |
| Role 5 starter validation | 100 starters fail |
| Role 5 requirement coverage | 1564 requirements covered |
| Role 5 mutation validation | 6092 killed, 49 equivalents, 0 survivors |
| Claude independent mutation run, 30 mutants per task | 2994 killed, 6 equivalents, 0 survivors |
| Public-file marker inspection | 0 private markers in 1321 public files |
| Private grader separation | 100 private grader directories; none shared between tasks |

These are attributed host findings, not proof that every possible mutation
or implementation was checked. Marker inspection does not replace the
per-run private-grader access audit.

### Calibration and known limitation

Under [decision 0008](decisions/0008-task-set-v2.md), the baseline A pilot
used the first 4 families, 20 tasks, on the Fast tier. Pass rate was 0.789
on 19 valid tasks, with CI 0.579 to 0.947. Task-level false done was 4 of
13 claimed-complete tasks. The remaining 16 families were designed harder;
no task was selected or dropped on its pilot outcome. This pilot is
calibration evidence and does not substitute for fresh full runs.

All 100 tasks follow one 16-requirement template over a 7-module package,
with the domain, normalization recipe, duplicate policy and error namespace
substituted per family. The set measures dense, interacting, explicitly
specified requirements, not varied task shapes.

## Freeze and reporting rules

Version 2 never changes. Any task-set change requires version 3 and a new
freeze record. Version 2 evaluation reports must carry the digest above in
`metadata.task_set_sha256`. [Version 1](eval-freeze.md) and its results remain
separate and unchanged.

After this freeze, no harness change may use version 2 results, per
[decision 0008](decisions/0008-task-set-v2.md). Run full A, B and harness
measurements fresh on frozen version 2 in W2, through 2026-11-06, retaining
the approved comparison scopes (B uses the 80 single-session tasks).
Final analysis is due 2026-11-13; disclose which version 1 runs informed the
2026-10-23 harness fixes.

Retain native evidence of the effective `service_tier = "priority"` (Fast)
for every version 2 configuration and pinned Standard-rate API-equivalent
cost accounting. Existing private-grader access audits and report/interface
rules continue to apply; this record changes no schema or interface.

## Assumptions

- Inventory, frozen metadata, digest, validation, calibration and limitation
  facts are the user-supplied Claude host findings dated 2026-10-24 at main
  commit `9097281`; this sandbox session does not independently verify them.
- The supplied pilot CI is recorded without assuming an unspecified
  confidence level or interval method.
