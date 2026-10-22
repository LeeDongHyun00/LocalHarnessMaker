# Evaluation task set version 1 freeze (D-3)

Frozen on 2026-10-22 at commit `7cdaf3b` (`feat(eval): freeze version 1 task set and reject unfrozen runs`). All 120 task `meta.json` files declare `"frozen": true` and `"version": 1`.

Task-set SHA-256:

```text
b78913b04280f6696d419d2afdc96b152675973d82f05199ddef848986285d1f
```

## Scope and inventory

The set contains 100 single-session tasks (25 each of bug fix, feature plus test, multiple requirements and constrained refactoring), plus 20 two-session tasks. The single-session set spans 25 related families across the four types. The exact inventory includes the legacy `bug-chunk-tail` task in the bug-fix group; there is no `bug-fix-ordinal-labels` task. The other three single-session types include `ordinal-labels`. Two-session tasks have metadata type `feature_plus_test`; they are counted separately here using `two_session: true`.

The table below records every task from [eval/tasks](../eval/tasks/) and its test-method counts from [GRADERS-PENDING.md](../eval/GRADERS-PENDING.md). Counts include errors as failures. All rows have validation status `validated`; reference counts match each task's `expected.json`. The earlier “All tasks remain unfrozen” sentence in GRADERS-PENDING.md predates this freeze; the frozen metadata and this record establish version 1.

| Group | Tasks | Private test methods |
|---|---:|---:|
| Bug fix | 25 | 123 |
| Feature plus test | 25 | 125 |
| Multiple requirements | 25 | 125 |
| Constrained refactoring | 25 | 125 |
| Two-session | 20 | 100 |

| Task ID | Public pass/fail | Reference pass/fail |
|---|---|---|
| bug-chunk-tail | 0/3 | 3/0 |
| bug-fix-adjacent-runs | 2/3 | 5/0 |
| bug-fix-balanced-brackets | 1/4 | 5/0 |
| bug-fix-clamp-values | 0/5 | 5/0 |
| bug-fix-common-prefix | 1/4 | 5/0 |
| bug-fix-flatten-once | 2/3 | 5/0 |
| bug-fix-inclusive-range | 1/4 | 5/0 |
| bug-fix-interleave | 1/4 | 5/0 |
| bug-fix-interval-union | 0/5 | 5/0 |
| bug-fix-invert-groups | 2/3 | 5/0 |
| bug-fix-last-index | 2/3 | 5/0 |
| bug-fix-line-endings | 1/4 | 5/0 |
| bug-fix-merge-counts | 2/3 | 5/0 |
| bug-fix-pairwise-edges | 2/3 | 5/0 |
| bug-fix-parse-pairs | 0/5 | 5/0 |
| bug-fix-partition-sign | 1/4 | 5/0 |
| bug-fix-prefix-sums | 1/4 | 5/0 |
| bug-fix-rotate-left | 1/4 | 5/0 |
| bug-fix-round-robin | 2/3 | 5/0 |
| bug-fix-select-columns | 0/5 | 5/0 |
| bug-fix-stable-unique | 2/3 | 5/0 |
| bug-fix-strip-prefix | 1/4 | 5/0 |
| bug-fix-unique-permutations | 1/4 | 5/0 |
| bug-fix-window-slices | 0/5 | 5/0 |
| bug-fix-word-counts | 1/4 | 5/0 |
| constrained-refactoring-adjacent-runs | 4/1 | 5/0 |
| constrained-refactoring-balanced-brackets | 4/1 | 5/0 |
| constrained-refactoring-clamp-values | 4/1 | 5/0 |
| constrained-refactoring-common-prefix | 4/1 | 5/0 |
| constrained-refactoring-flatten-once | 4/1 | 5/0 |
| constrained-refactoring-inclusive-range | 4/1 | 5/0 |
| constrained-refactoring-interleave | 4/1 | 5/0 |
| constrained-refactoring-interval-union | 4/1 | 5/0 |
| constrained-refactoring-invert-groups | 4/1 | 5/0 |
| constrained-refactoring-last-index | 4/1 | 5/0 |
| constrained-refactoring-line-endings | 4/1 | 5/0 |
| constrained-refactoring-merge-counts | 4/1 | 5/0 |
| constrained-refactoring-ordinal-labels | 4/1 | 5/0 |
| constrained-refactoring-pairwise-edges | 4/1 | 5/0 |
| constrained-refactoring-parse-pairs | 4/1 | 5/0 |
| constrained-refactoring-partition-sign | 4/1 | 5/0 |
| constrained-refactoring-prefix-sums | 4/1 | 5/0 |
| constrained-refactoring-rotate-left | 4/1 | 5/0 |
| constrained-refactoring-round-robin | 4/1 | 5/0 |
| constrained-refactoring-select-columns | 4/1 | 5/0 |
| constrained-refactoring-stable-unique | 4/1 | 5/0 |
| constrained-refactoring-strip-prefix | 4/1 | 5/0 |
| constrained-refactoring-unique-permutations | 4/1 | 5/0 |
| constrained-refactoring-window-slices | 4/1 | 5/0 |
| constrained-refactoring-word-counts | 4/1 | 5/0 |
| feature-plus-test-adjacent-runs | 0/5 | 5/0 |
| feature-plus-test-balanced-brackets | 0/5 | 5/0 |
| feature-plus-test-clamp-values | 0/5 | 5/0 |
| feature-plus-test-common-prefix | 0/5 | 5/0 |
| feature-plus-test-flatten-once | 0/5 | 5/0 |
| feature-plus-test-inclusive-range | 0/5 | 5/0 |
| feature-plus-test-interleave | 0/5 | 5/0 |
| feature-plus-test-interval-union | 0/5 | 5/0 |
| feature-plus-test-invert-groups | 0/5 | 5/0 |
| feature-plus-test-last-index | 0/5 | 5/0 |
| feature-plus-test-line-endings | 0/5 | 5/0 |
| feature-plus-test-merge-counts | 0/5 | 5/0 |
| feature-plus-test-ordinal-labels | 0/5 | 5/0 |
| feature-plus-test-pairwise-edges | 0/5 | 5/0 |
| feature-plus-test-parse-pairs | 0/5 | 5/0 |
| feature-plus-test-partition-sign | 0/5 | 5/0 |
| feature-plus-test-prefix-sums | 0/5 | 5/0 |
| feature-plus-test-rotate-left | 0/5 | 5/0 |
| feature-plus-test-round-robin | 0/5 | 5/0 |
| feature-plus-test-select-columns | 0/5 | 5/0 |
| feature-plus-test-stable-unique | 0/5 | 5/0 |
| feature-plus-test-strip-prefix | 0/5 | 5/0 |
| feature-plus-test-unique-permutations | 0/5 | 5/0 |
| feature-plus-test-window-slices | 0/5 | 5/0 |
| feature-plus-test-word-counts | 0/5 | 5/0 |
| multiple-requirements-adjacent-runs | 2/3 | 5/0 |
| multiple-requirements-balanced-brackets | 1/4 | 5/0 |
| multiple-requirements-clamp-values | 0/5 | 5/0 |
| multiple-requirements-common-prefix | 1/4 | 5/0 |
| multiple-requirements-flatten-once | 2/3 | 5/0 |
| multiple-requirements-inclusive-range | 1/4 | 5/0 |
| multiple-requirements-interleave | 1/4 | 5/0 |
| multiple-requirements-interval-union | 0/5 | 5/0 |
| multiple-requirements-invert-groups | 2/3 | 5/0 |
| multiple-requirements-last-index | 2/3 | 5/0 |
| multiple-requirements-line-endings | 1/4 | 5/0 |
| multiple-requirements-merge-counts | 2/3 | 5/0 |
| multiple-requirements-ordinal-labels | 1/4 | 5/0 |
| multiple-requirements-pairwise-edges | 2/3 | 5/0 |
| multiple-requirements-parse-pairs | 0/5 | 5/0 |
| multiple-requirements-partition-sign | 1/4 | 5/0 |
| multiple-requirements-prefix-sums | 1/4 | 5/0 |
| multiple-requirements-rotate-left | 1/4 | 5/0 |
| multiple-requirements-round-robin | 2/3 | 5/0 |
| multiple-requirements-select-columns | 0/5 | 5/0 |
| multiple-requirements-stable-unique | 2/3 | 5/0 |
| multiple-requirements-strip-prefix | 1/4 | 5/0 |
| multiple-requirements-unique-permutations | 1/4 | 5/0 |
| multiple-requirements-window-slices | 0/5 | 5/0 |
| multiple-requirements-word-counts | 1/4 | 5/0 |
| two-session-adjacent-runs | 0/5 | 5/0 |
| two-session-balanced-brackets | 0/5 | 5/0 |
| two-session-clamp-values | 0/5 | 5/0 |
| two-session-common-prefix | 0/5 | 5/0 |
| two-session-flatten-once | 0/5 | 5/0 |
| two-session-inclusive-range | 0/5 | 5/0 |
| two-session-interleave | 0/5 | 5/0 |
| two-session-interval-union | 0/5 | 5/0 |
| two-session-invert-groups | 0/5 | 5/0 |
| two-session-last-index | 0/5 | 5/0 |
| two-session-line-endings | 0/5 | 5/0 |
| two-session-merge-counts | 0/5 | 5/0 |
| two-session-pairwise-edges | 0/5 | 5/0 |
| two-session-partition-sign | 0/5 | 5/0 |
| two-session-prefix-sums | 0/5 | 5/0 |
| two-session-rotate-left | 0/5 | 5/0 |
| two-session-stable-unique | 0/5 | 5/0 |
| two-session-strip-prefix | 0/5 | 5/0 |
| two-session-window-slices | 0/5 | 5/0 |
| two-session-word-counts | 0/5 | 5/0 |

## Host verification evidence

The following private-grader results were verified by Claude on the host and supplied by the user. This documentation session checked the public inventory and counts; it did not rerun private grading or mutation tests.

From the repository root at the freeze commit, with the private grader root configured, Claude ran:

```sh
.venv/bin/python -m eval.runner.validate_graders --private-root "$LHM_PRIVATE_GRADERS" --tasks all
```

Result: 120 of 120 tasks valid, with the task-set SHA-256 above. The digest covers the git-tracked public inputs of every task plus the content hashes of its private graders, without including their locations. The private root path and grader contents are not recorded here.

Claude checked that no private path and no task-specific grader line appears in any public file. In an independent mutation test of the private references (1067 mutants), every inspected survivor in the twelve weakest tasks was behavior-equivalent. Role 5's own mutation mode reports zero non-equivalent survivors. These are attributed host findings, not a claim that every possible mutation or implementation was checked.

## Freeze and reporting rules

Under [Role 5 SC-2](../prompts/05-eval-engineer.md), version 1 never changes. Any task-set change requires a separate version 2 and a new freeze record. Evaluation reports must carry the digest above in `metadata.task_set_sha256`.

[Decision 4 of 2026-10-22](weekly/2026-10-21-host-verification.md#decisions-taken-on-2026-10-22) retains the task-cluster metrics specified by decision 0003. Claude's final evaluation also reports family-cluster bootstrap intervals, and a claim counts only if it holds under those intervals. This record does not change the report schema or interfaces.

## Assumptions

- The user-supplied Claude host results are the evidence for the private validation, digest, leakage inspection and mutation findings; this sandbox session independently checks public metadata and published counts only.
