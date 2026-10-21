# Role 5: Evaluation Engineer

Read AGENTS.md at the repository root first. This file is your contract.

## Goal

Produce the proof of the project: is "Sol at medium effort plus the harness" cheaper per passing task than "Sol at max effort alone", with equal or better quality. Build and freeze the task set, run baselines A, B and C and the proposed system with the same runner, and compute the metrics. The runner must not depend on the plugin hooks; the experiment must run even if the hooks break. Every number used in the presentation comes from your reports only.

## Ownership

Owned paths: eval/ including tasks/ (task set), runner/, baselines/, configs/, metrics.py, prices.yaml, reports/. Tests in tests/eval/.
Forbidden: editing controller/ or verifier/. Sharing task set contents with Role 3. After the freeze on 2026-10-27, send the task set hash to Role 1 for docs/eval-freeze.md.

## Interfaces

1. Other roles are called through their CLIs only: python -m controller contract, python -m verifier check, python -m controller handoff.
2. Executor model calls: codex exec "PROMPT" --sandbox workspace-write --json -o FILE. Re-instruction: codex exec resume SESSION_ID "REINSTRUCT_MESSAGE". Reasoning effort is set through the Codex configuration (the key model_reasoning_effort in config.toml; confirm the key name in the documentation of the installed version) and its actual application is confirmed from the --json event log.
3. Task directory: eval/tasks/ID/ containing prompt.md, workspace/ (initial state), hidden_tests/ (never visible to the executor; copied in only at grading time), expected.json (pass conditions), meta.json (type, difficulty, whether it is a two-session task).
4. Run configuration: eval/configs/NAME.yaml with model, reasoning effort, harness on or off, control backend, re-instruction limit, seed, Codex version.

## Deliverables

- D-1, due 2026-10-24: minimal runner that executes one task with codex exec and grades it with hidden_tests. Take the record from Role 2 on whether hooks fire under codex exec and reflect it in the runner design. Default design: the runner itself performs contract injection, verification and resume, without relying on hooks.
- D-2, due 2026-10-27: task set version 1 frozen. At least 100 tasks across the types bug fix, feature plus test, multiple requirements, and constrained refactoring. Plus 20 two-session tasks (day 1 prompt, then day 2 prompt). Sources: written by hand, or adapted from issues in small open-source repositories. Every task has hidden tests. Run baselines A (Sol medium alone) and B (Sol max alone) on a 10-task pilot first, report the cost, and run the full set after approval.
- D-3, due 2026-11-03: baseline C (static template: eval/baselines/template.md filled once by a human per task) and the proposed system with the cheap_api backend, first measurement, report version 1.
- D-4, due 2026-11-10: measurement with the local control backend, handoff success rate, and the table of 20 human-reviewed samples.
- D-5, due 2026-11-13: final report in eval/reports/final/ with tables and charts for pass rate, false done rate, cost per pass, attempts, and parity; results split by task type; sample sizes and bootstrap confidence intervals.

## Metric definitions (metrics.py)

- pass_rate: fraction of tasks where all hidden tests pass.
- false_done_rate: number of verdict items with reason claimed_without_evidence divided by the number of items that carried a done claim.
- cost_per_pass: (executor model cost plus control model cost, including re-instructions) divided by the number of passing tasks. Prices come from eval/prices.yaml.
- avg_attempts: mean number of attempts per task.
- handoff_success: fraction of two-session tasks where day 2 passes without the user restating the day 1 context.
- parity: pass_rate with the local control backend minus pass_rate with the cheap_api control backend.

## Success criteria

- SC-1: the runner executes one task end to end without human intervention and writes a result JSON. It supports retry, timeout, failure isolation, and resume after interruption.
- SC-2: the task set hash is recorded in docs/eval-freeze.md and the set never changes afterwards. A change requires a separate version 2.
- SC-3: every configuration runs on the same task set, the same seed and the same Codex version, and the run metadata is stored in the report.
- SC-4: the report states sample sizes and confidence intervals, and splits results by task type.
- SC-5: before any full run, a 10-task pilot is run and its cost estimate is reported and approved.
- SC-6: five baseline A results are re-checked by hand and the absence of grader errors is recorded.

## Verification

1. pytest tests/eval
2. python -m eval run --config eval/configs/pilot.yaml --out eval/reports/pilot/ and keep the log and the report.

## Stop and escalate conditions

In addition to STOP-1 to STOP-4 in AGENTS.md:
- STOP-E1: codex exec cannot complete a task non-interactively (it stops at an approval prompt, the sandbox rejects an action, and similar). Write candidate fixes and report immediately. If this cannot be solved, the whole comparison design must be redone.
- STOP-E2: the estimated cost of a full run exceeds the user's limit. Report before running.
- STOP-E3: there is evidence that Role 3 accessed the task set. Report the contamination.
- STOP-E4: a path is found through which hidden tests become visible to the executor model. Report it.

## First task

1. Create one task (bug fix with three hidden tests). Run it with codex exec in configuration A (medium effort) and automate grading. Confirm from the --json log that the reasoning effort was actually applied and record it.
2. Build the runner skeleton: configuration YAML, then the task loop, then result JSON, with resume support. Implement pass_rate in metrics.py.
3. Update state/STATUS-eval.md.
