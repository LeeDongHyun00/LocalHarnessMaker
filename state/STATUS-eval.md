## Done

- Added per-generation control accounting from hash-pinned stderr, actual backend/model and pinned eval rates, including retry/fallback and delegated judge calls; invalid task costs remain included (.venv/bin/python -m pytest tests/eval -q: 621 passed in 57.81s).
- Added null propagation for incomplete delegations, missing success records, interrupted/failed/deadline operations without complete accounting, and unpriceable models/tokens; metadata observes a single control model and warns otherwise (.venv/bin/python -m pytest tests/eval -q: 621 passed, including fallback, null cases, days, reinstructions and mixed models).
- Retained per-operation exit/deadline sidecars, archived interruption evidence and usage-limit recovery without rerunning completed executor work (.venv/bin/python -m pytest tests/eval -q: 621 passed, including existing usage-limit halt/recovery and interrupted handoff tests).
- Added smoke/full harness configs with reinstruction_limit 2; reduced B to 100 single-session tasks in A order; generalized exact-config estimate matching and published planning estimates (.venv/bin/python -m pytest tests/eval -q: 621 passed, including config population, 21/900 pre-judge call bounds and changed-config rejection).
- Recorded starting commit/pricing snapshot in new checkpoints; reports use starting commit, warn on drift and preserve legacy checkpoint behavior (.venv/bin/python -m pytest tests/eval -q: 621 passed, including start provenance, HEAD/pricing drift and legacy behavior).
- Updated eval/README.md and eval/CHANGES.md; only this worktree was edited, without staging or committing (git symbolic-ref --short HEAD: r5/harness-smoke; git rev-parse --short HEAD: b9ac131; git diff --check -- eval tests/eval state/STATUS-eval.md: exit 0; git diff --exit-code -- eval/tasks eval/reports/pilot-a eval/reports/pilot-b: exit 0).

## Remaining

- Integrate Role 4's verifier forwarding/delegation implementation outside this session; it is absent from this worktree. Claude runs smoke-harness on the host next, with the real private root and a fresh output directory.
- Confirm live accounting for contract/day-2 contract, judge retries/fallback, handoff, reinstruction, applied model/effort, audit evidence, termination, nested guards and developer_instructions delivery. Harness has never run live; mocked results do not establish compatibility.
- Complete the user-filled stratified 20-task C subset and baseline C measurement; run reduced B and full harness under the approved host workflow. Main checkout's full A run is already in progress and must remain isolated.
- Compare harness handoff_success with A. Keep local Gemma/QLoRA dropped and parity not measured; do not pursue the old local-comparator backlog.
- Complete the done-claim denominator, five valid pilot-A human reviews and 20-sample review/reporting; inspect historical pilot audit/version/cost evidence on the host before using it for comparison.
- Run the full repository suite once before a future merge. Only tests/eval ran here; no staging or commits.

## Decisions

- Consume controller/verifier stderr without changing their CLIs or shared schemas: user supplied the exact generation/delegation envelopes and Role 4 owns forwarding.
- Pin operation sidecars with control evidence: process exit/deadline state is needed to distinguish complete accounting from a killed or interrupted command, and must survive recovery.
- Reprice every observed generation with eval/prices.yaml: controller USD/pricing references are not the evaluation price snapshot; cache stays an input subset and reasoning stays inside output.
- Keep incomplete accounting null while retaining known per-call costs: invalid tasks and interrupted operations cannot silently disappear from costs.
- Preserve legacy checkpoint behavior and record provenance for new runs: a run's originating commit must not be replaced by end-of-run HEAD; pricing drift is reported with both snapshot IDs.
- Apply user-approved decision 0007 scope as supplied: C uses 20 stratified user-filled templates, B uses 100 singles, handoff compares with A, local/QLoRA are dropped and parity is not measured.
- Use pilot A session averages for requested executor planning estimates: full B additionally shows its historical max-effort pilot alternative; all figures are planning numbers, not measurements.

## Verify commands

- .venv/bin/python -m pytest tests/eval -q
- git diff --check -- eval tests/eval state/STATUS-eval.md
- git diff --exit-code -- eval/tasks eval/reports/pilot-a eval/reports/pilot-b
- Host only after Role 4 integration, fresh destination: .venv/bin/python -m eval run --config eval/configs/smoke-harness.yaml --out eval/reports/smoke-harness/
- Before future merge only: full repository suite once.

## Do not touch

- Main checkout or its running baseline A; edit only eval/, tests/eval/ and state/STATUS-eval.md in this worktree.
- Frozen eval/tasks/, retained measurements/pilots, controller/, verifier/, plugin/, shared schemas, CLI flags, root configuration and other roles' files. Never share tasks with Role 3.
- .git is read-only: no staging, commits, history rewrites or file deletion.
- No executor/controller/judge model calls, network, nested Codex, macOS sandbox-exec or real private-root lookup in this sandbox. Tests use synthetic graders only.
- Never backfill historical exit hashes, mutate source regrade runs, run Codex in grading copies or expose grader output to executor/controller context.

## Assumptions

- This session starts on r5/harness-smoke at b9ac131 with its own .venv. Decision 0007 is supplied by the user but not yet present here; no decision record or shared interface was edited.
- Role 4 will forward judge control_call/control_cli_events and exact judge_delegation records as specified; the runner treats missing/incomplete judge accounting as unknown. Live integration remains unverified.
- Failed commands with complete retained generation accounting can retain known costs; deadlines, negative/missing exits and incomplete streams remain unknown. Successful contract/handoff requires a success record.
- Planning Luna generations use 5,000 uncached input and 1,000 output tokens ($0.001 at the pinned rates); every day uses one pilot-A average session, with up to three attempts and three generations per control command.
- Starting snapshot ID is recorded for drift detection; report pricing still describes the snapshot actually used at report build. Old checkpoints are not migrated or backfilled.
- Freeze commit 7cdaf3b and population digest b78913b04280f6696d419d2afdc96b152675973d82f05199ddef848986285d1f remain authoritative. Historical pilots use 0.162; new configurations pin 0.163.0-alpha.11.1.
- Usage limits are no longer a planning constraint; the existing resumable halt remains necessary infrastructure behavior. No live measurement or spending approval is implied by config validation.
