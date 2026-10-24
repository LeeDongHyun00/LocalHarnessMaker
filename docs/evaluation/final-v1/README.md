# Final evaluation on task set version 1 (2026-10-24)

Written by Claude from the complete, priced version 1 reports on main at 9d5403e. This document closes the version 1 comparison; it supersedes docs/evaluation/interim-v1/. Version 1 is the 120-task set (100 single-session tasks in four types, 20 two-session tasks) that the harness was also debugged against, so this is a measurement of the harness on a task set it has seen, under the caveats below. The project verdict waits for version 2 (docs/eval-freeze-v2.md), which the harness has never been run against before the freeze.

Inputs, all status valid:

| Configuration | Report | Tasks | Pass | Fail | Total cost (USD) | cost_per_pass (USD) |
|---|---|---|---|---|---|---|
| Harness (Sol medium executor, gpt-6-luna control, 3 attempts per day) | eval/reports/full-harness-final3 | 120 | 119 | 1 | 5.175 | 0.0435 (CI 0.0395 to 0.0477) |
| A (Sol medium alone) | eval/reports/full-a-final3 | 120 | 117 | 3 | 3.849 | 0.0329 (CI 0.0298 to 0.0363) |
| B (Sol max alone, single-session tasks only) | eval/reports/full-b-recovered2 | 100 | 100 | 0 | 4.465 | 0.0447 (CI 0.0427 to 0.0467) |

Same task set digest and seed; codex-cli 0.163.0-alpha.11.1; executor on the Standard tier priced at snapshot openai-standard-short-2026-10-22-v1. Paired task-cluster bootstrap, 10000 resamples, seed 0, 95 percent intervals. Tables with every type: harness-vs-a.md and harness-vs-b.md; machine-readable harness-vs-a.json and harness-vs-b.json, which carry the sha256 of the source reports.

## Results

| Comparison | Pass rate, paired difference | cost_per_pass, paired ratio (harness over baseline) | Other |
|---|---|---|---|
| Harness vs A (n 120) | 0.992 vs 0.975; +0.017 (CI -0.017 to 0.050) | 1.32 (CI 1.26 to 1.39); by type bug_fix 1.37, constrained_refactoring 1.42, feature_plus_test 1.25, multiple_requirements 1.35 | handoff_success 0.95 vs 0.85 (n 20); task_false_done 0 of 20 vs 1 of 22 claimed-complete tasks; avg_attempts 1.23 vs 1.17 |
| Harness vs B (n 100) | 1.0 vs 1.0; 0 | 0.77 (CI 0.72 to 0.81); by type 0.81, 0.75, 0.74, 0.77, every interval below 1 | avg_attempts 1.05 vs 1.00 |

Reading, against the claim in CLAUDE.md section 5 (the harness must beat A and B on cost per passing task with equal or better pass rate):

- Harness vs B holds on version 1. Equal quality (every single-session task passes in both) at 77 percent of the cost, consistently across the four types. Sol medium with the harness replaces Sol max at a lower price on this set.
- Harness vs A does not hold on version 1. The harness costs 32 percent more per passing task, and the quality gain (+2 tasks of 120, both two-session) is inside the interval. Where the cost goes: the control calls are 7.1 percent of the harness total (0.369 USD); the rest is more executor work, chiefly re-instructed attempts (147 attempts against 140) and longer prompts carrying the contract. On single-session tasks A already passes 100 of 100, so there is nothing for the verifier to catch.
- The two-session tasks are where the harness helps on version 1: 19 of 20 pass against 17 of 20, with handoff_success 0.95 against 0.85 (intervals overlap, n 20). Cost on those 20 tasks: harness 1.753 USD, A 1.310 USD.
- Task-level false-done rate is near zero in every configuration (0 of 20, 1 of 22, 0 of 20 claimed-complete tasks), so version 1 cannot measure the verifier's main purpose. The version 2 calibration pilot measured 4 of 13 for A on harder tasks; version 2 is the set that can answer this.

Verdict for version 1: the harness is a cheaper substitute for maximum effort (B) and a more expensive, not measurably better, addition to medium effort (A) on a task set that medium effort already saturates. The project claim is therefore half proven on version 1 and cannot be fully proven on it; version 2 decides.

## What was and was not verified by a human

- Hidden grading, cost accounting, access audits and the paired comparison are automated; Claude verified the tooling on the host (tests/eval 1755 passed at 9d5403e) and spot-checked audit records and runtimes during the recovery rounds.
- Human review of sampled verdicts has not been done: docs/evaluation/human-review-sample-full-a.md (22 tasks) and human-review-sample-full-harness.md (20 verdicts) are prepared for the user. Until then the pass counts rest on the hidden graders and the three regrade passes.
- The user has not filled the 20 C templates (eval/baselines/c/), so baseline C (static template) is not compared here.

## Caveats and disclosures

- Harness fixes informed by version 1 runs: after the two-task smoke and a 21-task harness run on version 1 (kept as full-harness-v1-partial and smoke-harness-attempt2), the contract prompt, contract validation and the retry rule were changed, and the run reported here followed those changes. Version 1 harness numbers are therefore optimistic relative to an unseen set. The version 2 freeze (decision 0008) forbids any harness change that uses version 2 results.
- Recovery provenance: the three reports are regrades or reruns of interrupted runs (host restarts, an audit false positive, a bytecode hash defect). One task per run was rerun or continued; per-task provenance is in each report directory (run-diagnostics.json, continuation.json, rerun files). full-harness-final3 derives from full-harness-recovered4, full-a-final3 from full-a-continued2.
- Control pricing: gpt-6-luna ran at its default priority (Fast) tier but is priced at Standard rates in these reports. Sensitivity: at Fast rates the control cost doubles to about 0.74 USD, the harness total becomes about 5.54 USD and the ratio against A about 1.42; the ratio against B becomes about 0.82. The direction of both results is unchanged.
- Audit precision: 17 rounds of audit-parser fixes during recovery; every unresolved record turned out to be a parser or path-comparison defect, never a grader access. The regrade passes on main 9d5403e report every task's audit clean.
- Single run per configuration; no repetition across seeds. Intervals describe task sampling, not run-to-run variance.
