# Interim evaluation on task set version 1 (2026-10-24)

Written by Claude from the recovered version 1 reports on main at 51d2e52. Interim: the overall cost metrics are still undefined because one task per run has no cost yet (restart casualties and a fresh rerun whose control calls are unpriced; r5-fixes-005 and the running recovery chain resolve this). Per-type cost ratios are complete for bug_fix and constrained_refactoring and are reported here. Nothing in this directory is a headline result.

Inputs, all valid under the approved rule: harness = eval/reports/full-harness-recovered3 (120 tasks, Sol medium plus gpt-6-luna control, 3 attempts per day); A = eval/reports/full-a-continued2 (120 tasks, Sol medium alone); B = eval/reports/full-b-regrade (100 single-session tasks, Sol max alone). Same task set digest, seed and codex-cli 0.163.0-alpha.11.1. Paired task-cluster bootstrap, 10000 resamples, 95 percent intervals. Tables: harness-vs-a.md and harness-vs-b.md.

## What the numbers say

| Comparison | Pass rate (paired difference) | Cost per pass (paired ratio, harness over baseline) | Other |
|---|---|---|---|
| Harness vs A | 0.992 vs 0.975; +0.017 (CI -0.017 to 0.050), n 120 | bug_fix 1.37 (1.23 to 1.52); constrained_refactoring 1.42 (1.29 to 1.57); overall undefined | handoff_success 0.95 vs 0.85 (n 20); task_false_done 0 of 20 vs 1 of 22 |
| Harness vs B | 1.0 vs 1.0; 0, n 100 | bug_fix 0.81 (0.72 to 0.91); constrained_refactoring 0.75 (0.69 to 0.83); overall undefined | avg_attempts 1.05 vs 1.01 |

- Against B (max effort alone) the harness delivers the same quality at about 75 to 81 percent of the cost on the two complete types. That part of the project claim holds on version 1 so far.
- Against A (medium effort alone) the harness costs 37 to 42 percent more with no significant quality gain on single-session tasks, because A already passes every single-session task. The difference sits in the two-session tasks, where the harness recovers more day-1 context (19 of 20 against 17 of 20), inside overlapping intervals.
- The version 1 ceiling is why version 2 exists. The task-level false-done rate on version 1 is near zero for every configuration; the version 2 pilot showed 4 of 13 claimed-complete tasks failing for A, which is where the harness's verifier should matter.

## Caveats

- The harness code was fixed during the day after two live runs on version 1 tasks (smoke on two tasks, harness v1 on 21 tasks); those runs are retained as diagnostics (full-harness-v1-partial, smoke-harness-attempt2). The version 2 freeze forbids any further harness change informed by version 2 results.
- One task per run was rerun or continued after a host restart or an audit fix; provenance is in each report's run-diagnostics.json and continuation.json.
- Control calls ran at gpt-6-luna's default priority tier but are priced at Standard rates in version 1 reports.
- Human review of the sampled tasks (docs/evaluation/human-review-sample-*.md) has not been done yet.
