## Done

- Added optional task_root with the historical eval/tasks default, per-set population/freeze/digest handling, cross-set comparison refusal, and selected-root regrade/day-2/audit support; added optional service_tier on all executor launches with per-process native applied-tier verification and explicit invalidation (final `.venv/bin/python -m pytest tests/eval -q`: 1058 passed in 122.14s).
- Wrote eval/tasks-v2/DESIGN.md before construction; built four families, twenty unfrozen tasks, public regression workspaces and external graders/references; retained numbered requirement coverage and actual generated verification reports (offline eval.runner.validate_graders.validate_task over all configured v2 IDs: 20 valid, 245 reference checks passed, 20 starters rejected, 252/252 requirements covered; eval/reports/pilot-v2-validation.md).
- Exhaustively graded all current AST mutants, strengthening specification-derived checks where needed; privately reviewed and hash-bound equivalent cases (offline eval.runner.validate_graders.mutate_task with limit 100000 over all 20 v2 IDs: 1090 killed, 10 equivalent, 0 unclassified survivors; 20/20 starter public regressions and 20/20 reference verification commands passed).
- Added eval/configs/pilot-v2-a.yaml and its STOP-3 estimate: full A model/effort, priority, pinned Codex version, 900/1800-second per-process deadlines, retry_limit 0 and 24 planned launches; updated eval README/CHANGES (candidate/config tests in final `.venv/bin/python -m pytest tests/eval -q`: 1058 passed in 122.14s).
- Preserved the previously committed literal-JavaScript audit and day-2 continuation work and version 1 public inputs (`git diff --exit-code -- eval/tasks`: exit 0; prior `.venv/bin/python -m pytest tests/eval -q`: 1023 passed in 97.92s).

## Remaining

- Host: review the v2 candidate and priority pricing, commit it, apply an explicitly reviewed candidate freeze and obtain spending approval before the 24-session baseline-A calibration. No executor/controller/judge call was made here. Target roughly 30–70%; revise difficulty across entire families/types, retain every candidate and never select/drop tasks by individual pilot outcome.
- After calibration: build the remaining sixteen planned families, validate the resulting full population, and publish its separate freeze through Role 1. All current v2 metadata remains frozen=false as requested.
- Preserve main-checkout measurements. Transfer this worktree only when the host can avoid changing code under active runs; do not reinterpret v1 outcomes as matched v2 quality evidence.
- Host: retain the earlier re-audit/day-2 continuation follow-up, C authored once by the user, reduced B and harness measurement workflow, paired comparisons, five pilot-A reviews and twenty-sample reporting. No host outcome recovery is claimed in this worktree.
- Run the full repository suite once before merge on the host. Only tests/eval was run here. No staging or commits; use the final Commit plan.

## Decisions

- Keep default v1 digest bytes and absent-tier CLI behavior: optional config fields do not migrate old reports or alter frozen task files.
- Namespace nondefault-root digests and select inputs consistently for execution/recovery: reports from different task sets must not compare, and population fingerprints must cover the selected set.
- Verify service_tier from native thread_settings_applied for every executor process, including fresh day 2 and resumed/retried launches: a request or turn_context alone is insufficient; missing/different evidence invalidates before grading.
- Keep priority costs null under the existing Standard-only snapshot: the historical Standard average is a workload proxy, not verified priority pricing.
- Publish numerical validation by task ID only: private graders, references, coverage and mutation rationale remain external. V2 equivalences bind day-2 bytes as well as reference/specification identities.
- Preserve task-cluster statistics in the approved schema and family metadata in the public population: family sensitivity analysis is planned without changing the shared report interface.

## Verify commands

- .venv/bin/python -m pytest tests/eval -q
- .venv/bin/python -m pytest tests/eval/test_v2_support.py tests/eval/test_validate_graders.py tests/eval/test_telemetry.py -q
- git diff --check -- eval tests/eval state/STATUS-eval.md
- git diff --exit-code -- eval/tasks
- Host/offline: .venv/bin/python -m eval.runner.validate_graders --private-root "$LHM_PRIVATE_GRADERS" --tasks CONFIGURED_V2_IDS
- Host/offline mutation validation: add --mutants 100000 to the preceding command; CONFIGURED_V2_IDS means all twenty IDs in eval/configs/pilot-v2-a.yaml, not the literal placeholder.

## Do not touch

- Work only in r5/v2 with this worktree's .venv; edit only eval/, tests/eval/, this status file and authorized external private storage. Preserve the main checkout and other roles' work.
- Frozen eval/tasks/, version 1 graders, retained historical reports, schemas, controller/, verifier/, plugin/, root configuration and existing CLI flags. Never share task contents with Role 3.
- .git is read-only: no staging, commits, history rewrites or project-file deletion.
- No live executor/controller/judge calls, network, nested Codex or macOS sandbox-exec in this session. Mock executor/control operations; ordinary local trusted grader/reference subprocesses are permitted.
- Never execute or resume Codex in a grading copy, publish private locations/content, fabricate accounting or clear incomplete historical audit evidence through a later successful session.
- Keep C skeletons unfilled until the user authors them; do not revise templates after C starts. Keep all v2 task metadata unfrozen until a reviewed host candidate-freeze step.

## Assumptions

- Full A's 115/120 outcome, including 100/100 singles, is user-supplied context; no retained host result was inspected or rewritten here. Version 2 quality and its target difficulty remain unmeasured.
- Deadlines apply to each executor process: 900 seconds for a single-session task and 1800 seconds per day/process of a two-session task.
- The current offline price snapshot covers Standard only. No priority rate is inferred, and the STOP-3 estimate leaves priority USD unknown pending host verification.
- Final-response honesty still requires retained executor-event observation; the generated public verification artifact and reproduced counts cannot independently prove when a command ran.
