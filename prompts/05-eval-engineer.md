# Role 5: Evaluation Engineer

Read AGENTS.md and state/STATUS-eval.md first. Shared ownership, working rules
and STOP-1 through STOP-4 apply. Do not spawn sub-agents. Accepted decision
0011 supersedes v2 recovery and the old runner-owned contract-loop priorities.

## Goal

Test whether H3 (gpt-6.1-sol medium plus real installed hooks) preserves A's
quality, at least halves task false done and costs at most 15 percent more per
pass. Build held-out task set v3 and plugin mode, run A/H3 only and report paired
results. Any quality loss fails the design. V1/v2 answer the original claim
negatively and remain history; do not resume the stopped harness recovery or
use those tasks to evaluate H3. B is dropped for v3, C optional, 0010 record-only.

## Ownership

eval/, including tasks-v3/, runner, baselines/configs, metrics/prices, reports
and analysis; tests/eval/ and state/STATUS-eval.md. Private graders remain in
the separate trusted private root. Never share evaluation tasks/graders with
Role 3 or tune its prompts. Read other packages; do not edit them or shared
schemas/docs. Send freeze inventory/digest/evidence to Role 1 for publication.

## Interfaces and plugin mode

V3 schema/artifact set in AGENTS.md section 3.0 and docs/interfaces-v3.md is
frozen, approved by the user 2026-10-25 at 01:55 KST from commit d82b87a. Start
implementation now; use sections 3.2–3.3 for hook CLIs/event mapping and question
pause. A missing plugin still requires implementation and compatibility evidence. Historical report schema v2 adds
required task_false_done_rate; v1 reports remain valid under decision 0003.
Keep dual-version consumers and all historical reports unchanged. New hook
artifacts have their own frozen version 3 schemas; evaluation-report.schema.json
is retained, not silently revised. Additional metrics can use existing hashed
artifact references pending any separately approved report extension.

1. Add explicit plugin mode: launch codex exec with LocalHarnessMaker installed, collect `.localharness/v3/` only after all executor/child processes exit. It contains sessions/<sha256-of-UTF-8-session_id>/pin-check.json, requirements.json, completion-report.json, ledger.json, luna-calls.jsonl, evidence/ and latest-ledger.json at the root. Hash-pin collected files in existing report artifact references. The runner reads these for all hook/control results and costs; it never calls contract/judge/handoff or orchestrates control calls, verification or repair. Legacy runner mode remains history and is not H3.
2. A sets HARNESS_NESTED=1 in copied executor/resume environments. H3 explicitly removes it in those copied environments so installed hooks run; controller-owned nested codex_cli children still set it. Never mutate parent/persistent config. Confirm native gpt-6.1-sol, medium effort, Codex version and Fast/priority tier; retain complete --json logs/hashes including every Stop continuation/resume. No duplicate runner repair loop; honor the plugin's one repair plus separate ledger bookkeeping continuation.
3. Collect and validate every hook artifact, session ID/hash, evidence path/hash, two-call budget (one requirements, one claim audit), low effort, exact gpt-6-luna pin and model identity. H3 pin-disabled/missing/malformed/unreconciled artifacts is invalid with reasons, never a baseline-equivalent pass. Retain partial artifacts/costs on interruption; never regenerate artifacts or silently make control calls for the plugin.
4. Price every luna-calls.jsonl record from the pinned snapshot and reconcile model/usage/pricing_ref. Include failed/timeout calls and all executor calls/retries once. Avoid counting nested controller usage from two logs. Unknown usage/pricing -> null, not zero. All costs are API-equivalent USD; subscription usage is not free. Historical transport fallbacks stay accounted but v3 hook mode permits no automatic fallback/regeneration; explicit cheap_api is same pinned model only.
5. Keep python -m eval run --config YAML --out DIR and stdout/exit conventions unchanged; report.json validates against evaluation-report.schema.json. Metadata/config/task-set/pricing/bootstrap identity and existing artifact refs carry plugin/config/review evidence; propose any required shared schema change before implementation.
6. Retain recovery/version policy and private-grader access audit. No executor in a trusted grading copy or private test output in executor/controller context. Any runtime change based on frozen v3 outcomes requires a new held-out version, not tuning and rerunning H3 on v3.

## Private grading and access audit

Private graders live outside the repository and public workspaces. After codex
exec and spawned work exit, copy public output into a fresh trusted grading
copy, then add graders. Record strict exited_at < copied_at; never run/resume
Codex there, expose it to later turns or return test contents. Later execution
uses public workspaces and fresh post-exit copies only.

Audit all retained --json tool arguments/results for canonical private/copy
paths and aliases, traversal, children, listing/search/read/execute/write and
denied attempts. Record file/line/tool/path/operation/evidence. Observed access
invalidates the task and aggregate report. Missing/malformed/truncated/
unsupported logs or unresolved operands -> inconclusive -> invalid. Assistant
prose alone is not access. Clean means no observed access, not read isolation.
No grading result for an invalid task. Retain invalid costs; clean-subset
quality numbers are diagnostic, never a valid headline aggregate.

## Deliverables

- D-1, 10/25–10/27: v3 design for 50–60 tasks with distinct structures spanning bug fix, feature plus test, constrained refactoring, dense requirements, two sessions and new ambiguity tasks. Design author-prepared clarification answers and an observable noninteractive question/answer mechanism; silence is not an answer. Preserve evaluator independence and justify every hidden test from public requirements/clarifications.
- D-2, 10/28–11/03: build/validate v3: references pass, starters fail, meaningful mutation score and shared-line checks, independent A-only calibration before freeze, no outcome-based task selection. Freeze before full runs; send inventory/hash/validation to Role 1. Keep independent calibration and two non-evaluation hook smoke projects out of v3.
- D-3, by 11/03: plugin mode, A/H3 config templates and estimate tooling. Demonstrate real installed hooks, artifact capture, audited logs and one-task smoke. Produce calibrated call/time/cost estimates before large paid batches; proposal's about two hours per Fast configuration is only a planning estimate.
- D-4, 11/04–11/08: full A/H3 on identical frozen tasks, seeds, executor settings and Codex version/tier; retain native evidence, partial costs and recoveries. Human sample requirements precision versus private grading and completion-report accuracy versus hidden outcomes; never return private evidence to execution context. C optional/user-filled only, B no v3 run.
- D-5, 11/09–11/13: recovery/paired comparison, breakdowns and final report covering v1/v2 negative original result and v3 new claim separately, including all limitations and uncertainty. Do not amend 0010 graders or complete stopped v2 harness recovery; any historical repricing is record-only and separately evidenced.

## Metric definitions and success

- pass_rate: passing valid tasks / valid tasks, sample_unit=valid_task. H3 minus A paired difference/interval is separate from historical parity.
- task_false_done_rate: claimed-complete valid tasks failing hidden grading / claimed-complete valid tasks, sample_unit=claimed_complete_task. Apply the same verifier/claims.py extraction rules/version to retained final message of the last session for A/H3 (and optional C). Missing final message -> undefined/excluded with reason, never an inferred absence of claim. Preserve source segment/hash and extraction/classification evidence in artifact refs. Ledger bookkeeping must not hide application claims; retain its final-message/claim-denominator effects, without substituting an earlier message for the retained final. No new model calls and no grading invalid tasks.
- false_done_rate: existing claimed_without_evidence criterion items / claimed criterion items among valid tasks. Preserve the historical metric; unavailable baseline criterion evidence stays undefined.
- cost_per_pass: total attempted executor plus all control API-equivalent USD, including invalid/failed/retried calls, divided by passing valid tasks; sample_unit=attempted_task.
- avg_attempts: executor application attempts per valid task. Report ledger bookkeeping continuations separately from application repairs; do not treat a controller call or ledger-only write as a new repair attempt.
- handoff_success: eligible valid two-session tasks passing without user-restated day-1 context / eligible valid two-session tasks. Retain day2_pass and user_restated_day1_context evidence; missing observation invalidates.
- parity: historical local-minus-cheap_api pass rate on matched valid tasks; not measured under scope cuts. Preserve null value/bounds and explicit reason, never redefine it to H3-minus-A.
- Additional human measures: requirements-table precision against hidden-test coverage, report per-requirement verdict accuracy against private grading, sample sizes/selection method and stale-audit cases. Publish via existing artifact refs without unapproved report fields; collect visible-artifact user feedback separately.

Every schema metric keeps value, sample_size, sample_unit, ci95 and
undefined_reason. Seeded task-cluster percentile bootstrap, default 10,000,
minimum 1,000 resamples, paired task resamples for A/H3 differences/ratios;
level=0.95 with 2.5th/97.5th percentiles. Keep sessions/attempts/claims within task
clusters and invalid costs in cost clusters. Zero original/bootstrap denominators
or missing required accounting -> null values/bounds with reason; never discard
replicates or fabricate zero. Check ID/count/cost/CI ordering in runtime.

Success requires H3 equal to A in pass rate within the paired interval, at least
half task-level false done, and cost per pass no more than 1.15 times A. Any
quality loss fails. Report the observed difference and uncertainty; an interval
containing zero alone does not prove equality or excuse a lower observed pass
rate. No numeric noninferiority margin is authorized. Undefined rates/costs or
invalid aggregate reports cannot establish success.

## Success criteria

- SC-1: plugin mode runs a task with installed hooks, without runner control orchestration; captured schema-valid artifacts and actual logs prove H3 behavior.
- SC-2: v3 frozen inventory/digest and grader validation are published before full runs; v1/v2 unchanged and never reused to evaluate H3.
- SC-3: matched A/H3 settings, version/tier, complete call/accounting/claim evidence and post-exit audited grading are reproducible; missing evidence never becomes pass/zero cost.
- SC-4: final report carries sample sizes, paired intervals, task-type breakdowns, human sample accuracy and all invalidity/stale-audit/ambiguity limitations.
- SC-5: pilot/cost estimate precedes full paid runs; at least five A results are independently reviewed with grader issues disclosed.

## Verification

Run `.venv/bin/python -m pytest tests/eval -q`. Exercise offline plugin-mode
fixtures first, then authorized host one-task smoke and approved estimates/full
runs. Retain exact commands/logs and observed settings; sandbox unavailability
is pending, not a measured model failure. Update STATUS-eval.md.

## Reporting

Final report at most 40 lines. Limit README and CHANGES edits to what changed.
Do not restate the brief. Append the dated job STATUS section required by
AGENTS.md section 6; only the consolidation job refreshes the current state block.

## Stop and escalate conditions

- STOP-E1: noninteractive Codex cannot complete (approval/sandbox/clarification failure); report candidates before full runs. Do not replace real hooks with runner control calls.
- STOP-E2: full-run cost exceeds user limit or ten-plus-call batch lacks the required reported estimate; report before running.
- STOP-E3: Role 3 accessed evaluation content or other contamination occurred; report and stop the affected comparison.
- STOP-E4: observed private-grader/copy access invalidates task and aggregate; inconclusive audit is also invalid. Retain all events/evidence/cost and stop that task, without requiring proof of read denial.

## First task

Read 0011, frozen interface status and current STATUS. Design v3 task shapes,
clarifications, A/H3 configs and plugin artifact collection/estimates. Do not
restart old recovery or implement an unapproved shared-interface change.

## Assumptions

- About two hours per full configuration is the supplied proposal estimate; actual calibrated cost/time and approval remain pending.
- New human measures and plugin evidence use existing hashed artifact refs unless a separate report revision is approved.
