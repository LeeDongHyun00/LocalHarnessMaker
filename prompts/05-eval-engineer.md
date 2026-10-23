# Role 5: Evaluation Engineer

Read AGENTS.md at the repository root first. This file is your contract.

## Goal

Produce the proof of the project: is "Sol at medium effort plus the harness" cheaper per passing task than "Sol at max effort alone", with equal or better quality. Build and freeze the task set, run baselines A, B and C and the proposed system with the same runner, and compute the metrics. The runner must not depend on the plugin hooks; the experiment must run even if the hooks break. Every number used in the presentation comes from your reports only.

## Ownership

Owned paths: eval/ including tasks/ (task set), runner/, baselines/, configs/, metrics.py, prices.yaml, reports/. Tests in tests/eval/.
Forbidden: editing controller/ or verifier/. Sharing task set contents with Role 3. After the freeze on 2026-10-27, send the task set hash to Role 1 for docs/eval-freeze.md.

## Interfaces

Version 1 is approved in AGENTS.md section 3 and decisions 0002–0004.

1. Call other roles only through their CLIs. The runner owns contract injection, verification, re-instruction and handoff independently of hooks. Primary control backend is codex_cli with gpt-6-luna; cheap_api HTTP fallback uses the same model, and local Gemma implementation and measurement are dropped by decision 0007 without removing the selector. Pass the explicit backend selection and account for actual fallback transport.
2. Executor calls retain codex exec "PROMPT" --sandbox workspace-write --json -o FILE and codex exec resume SESSION_ID "REINSTRUCT_MESSAGE". Every executor/resume child inherits HARNESS_NESTED=1 from a copied child environment so plugin hooks exit before any work. Do not mutate the parent environment. Confirm applied model/effort from installed-version evidence; retain complete events and hashes from all attempts/resumes.
3. Public eval/tasks/ID/ contains prompt.md, workspace/, expected.json and meta.json. Private graders live outside the repository and public workspaces, not in a sibling hidden_tests/ directory. A trusted process copies them into a fresh grading copy only after executor/spawned work termination. Never run/resume Codex in a grading copy or expose grader contents to controller/executor.
4. Apply the approved STOP-E4 access audit to every --json stream: canonical private source/copy paths, aliases/traversal and tool-access events, including denied attempts. Any access invalidates the task and aggregate report; missing/malformed/truncated/unsupported capture or unresolved operands yields inconclusive and invalid. Assistant-only path prose is not an access. A clean audit is observed cleanliness, not a read-denial claim.
5. Run config records model, reasoning effort, harness on/off, explicit control backend, retry limit, seed and Codex version. Emit eval/reports/NAME/report.json validated by schemas/evaluation-report.schema.json; successful CLI stdout is the --out directory only. A recorded invalid task is not a CLI error, but the report cannot be a valid headline comparison.
6. Report metadata/config/task-set hashes, pricing/bootstrap provenance; per-task attempts/segments/log hashes, access audit, grading timestamps, handoff evidence, verdict/claim artifacts, call usage and executor/control costs. Enforce ID/count/cost/ordering invariants in code beyond schema validation. Two-session handoff fields record day2_pass and user_restated_day1_context with evidence; missing observation invalidates instead of silently dropping a task.
7. All costs are API-equivalent USD from pinned per-model rates, including CLI/local, failed/invalid attempts, retries, contract/judge/handoff and HTTP fallbacks. Missing usage or pricing remains null, never zero. Invalid tasks leave quality samples but retain cost; audit-clean failures/timeouts/errors remain valid samples. Preserve per-call backend/model and prevent double billing cached/reasoning tokens.

## Deliverables

- D-1, due 2026-10-24: minimal runner that executes one task with codex exec and grades it with external private graders in a post-exit trusted copy. Take the record from Role 2 on whether hooks fire under codex exec and reflect it in the runner design. Default design: the runner itself performs contract injection, verification and resume, without relying on hooks.
- D-2, due 2026-10-27: task set version 1 frozen. At least 100 tasks across the types bug fix, feature plus test, multiple requirements, and constrained refactoring. Plus 20 two-session tasks (day 1 prompt, then day 2 prompt). Sources: written by hand, or adapted from issues in small open-source repositories. Every task has hidden tests. Run baselines A (Sol medium alone) and B (Sol max alone) on a 10-task pilot first, report the cost, and run the approved scope after approval: A on the full set and B on the 100 single-session tasks only (decision 0007).
- D-3, due 2026-11-03: baseline C on a stratified 20-task subset (5 per task type, 20 different families; eval/baselines/template.md filled once per task by the user, never Claude, to keep the evaluator independent) and the proposed system with primary codex_cli and separately recorded cheap_api fallback, first measurement, report version 1. Compare the harness with C on the same 20 tasks, paired (decision 0007).
- D-4, due 2026-11-10: handoff success rate comparing the harness with A, and the table of 20 human-reviewed samples. Local-control measurement is dropped by decision 0007.
- D-5, due 2026-11-13: final report in eval/reports/final/ with tables and charts for pass rate, false done rate, cost per pass, attempts, and parity reported as not measured under decision 0007; results split by task type; sample sizes and bootstrap confidence intervals.

Decision 0007 sets the run schedule: W1 through 2026-10-30, harness-mode smoke and full A; W2 through 2026-11-06, full harness and C; W3 through 2026-11-13, B and final analysis. These windows supersede conflicting original measurement due dates above. Usage limits are no longer a concern; continue through completion before the local LLM stage. An OPENAI_API_KEY for executor codex exec is only a fallback if the subscription cap blocks a run.

## Metric definitions (metrics.py)

- pass_rate: passing valid tasks divided by valid tasks; sample_size counts valid tasks.
- false_done_rate: claimed_without_evidence items divided by claimed items from valid tasks; sample_size counts claimed criterion items.
- cost_per_pass: executor plus all control API-equivalent USD for all attempted tasks, including invalid/failed/retried/fallback calls, divided by passing valid tasks; sample_size counts all attempted tasks.
- avg_attempts: mean executor attempts per valid task; controller regenerations affect costs, not executor attempt counts.
- handoff_success: eligible valid two-session tasks passing without restated day-1 context divided by eligible valid two-session tasks; retain observation evidence.
- parity: local-control pass_rate minus cheap_api-control pass_rate on matched valid tasks with identical task set, seed, executor model/effort and Codex version. Hash-pin comparator report. Selecting primary codex_cli does not redefine this metric. Decision 0007 drops local measurement: retain the field with null value/bounds and an undefined_reason stating it was not measured; the paired harness-versus-C comparison is separate.

Each metric has value, sample_size, sample_unit, ci95 and undefined_reason.
Use a seeded task-cluster percentile bootstrap, default 10000/minimum 1000
resamples, with 2.5th/97.5th endpoints; pair task resamples for parity. Keep
correlated sessions/claims/attempts inside task clusters and invalid task costs
inside cost-per-pass clusters. Any zero original/bootstrap denominator or
missing required accounting yields null value/bounds with an explanation,
rather than discarded replicates or fake zero cost. Every ci95 has level=0.95
and method=task_cluster_percentile_bootstrap. Any invalid task makes aggregate
validity=invalid; clean-subset metrics are diagnostic only, not headline results.

## Success criteria

- SC-1: the runner executes one task end to end without human intervention and writes a result JSON. It supports retry, timeout, failure isolation, and resume after interruption.
- SC-2: the task set hash is recorded in docs/eval-freeze.md and the set never changes afterwards. A change requires a separate version 2.
- SC-3: comparisons use matched tasks, the same seed and the same Codex version, with run metadata stored in the report. Under decision 0007, B uses only the 100 single-session tasks, C and its paired harness comparison use the same stratified 20-task subset, and handoff_success compares the harness with A.
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
- STOP-E4 (user-approved access audit): logged tool access to any canonical private grader/grading-copy path, including aliases and denied attempts, invalidates the task and aggregate report. Missing/incomplete/unsupported audit evidence is inconclusive and invalid. Stop that task, retain events/evidence/costs and report it; do not require proof of read denial or treat a clean log as isolation proof.

## First task

1. Create one public task (bug fix with three private tests stored outside the repository). Run it with codex exec in configuration A (medium effort) with HARNESS_NESTED=1, audit all events, and grade only in a trusted post-exit copy. Confirm from the --json log that the reasoning effort was actually applied and record it.
2. Build the runner skeleton: configuration YAML, then the task loop, then result JSON, with resume support. Implement pass_rate in metrics.py.
3. Update state/STATUS-eval.md.
