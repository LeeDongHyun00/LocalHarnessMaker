# Role 2: Plugin Engineer (hooks and skill)

Read AGENTS.md first and state/STATUS-plugin.md. Shared ownership, working rules
and STOP-1 through STOP-4 apply. Do not spawn sub-agents. Continue Remaining
under accepted decision 0011, which supersedes old contract-loop work.

## Goal

Run the pinned-Luna hooks in real Codex sessions: pin-check, visible requirements
and questions, deterministic completion/single repair, executor ledger and next
session injection. Preserve process hygiene, installation and version policy.
Do not implement a second verification loop in the plugin.

## Ownership

plugin/, including hooks/configuration, skill, templates, installer, demo,
verified-version registry/evidence; tests/plugin/ and state/STATUS-plugin.md.
Read everything else. Propose shared docs/interface changes for Role 1; never
edit controller/, verifier/, eval/ or other roles' STATUS.

## Interfaces

The version 3 set in AGENTS.md section 3.0 and docs/interfaces-v3.md is frozen,
approved by the user 2026-10-25 at 01:55 KST from commit d82b87a. Start implementation now.
Use the frozen hook CLIs and event mapping in AGENTS.md sections 3.2–3.3.
Direction 0011 is already accepted. Historical CLIs/schemas stay unchanged for
v1/v2 consumers; new hooks do not call contract, handoff or judge generators.

- Use `.localharness/v3/sessions/<sha256-of-UTF-8-session_id>/` for pin-check.json, requirements.json, completion-report.json, ledger.json, luna-calls.jsonl and referenced evidence/. Revalidate `.localharness/v3/latest-ledger.json` before injection. Atomic JSON writes, confined paths and verified hashes; do not inject a stale ledger.
- Preserve measured SessionStart/UserPromptSubmit additionalContext and Stop decision=block/reason formats. SessionEnd is observe-only. Obtain version compatibility evidence before optional PreToolUse; propose any new wire fields instead of inventing them.
- Every hook first checks exact `HARNESS_NESTED=1` and exits 0 with zero bytes on stdout AND stderr before stdin/import/config/files/logging or exception handling. H3 executors leave it unset; controller children set it. Mock both paths.
- Pin exact gpt-6-luna with verified CLI version/model-list and pinned pricing coverage. Missing/unobservable/renamed pin writes a visible pin-check advisory and disables Luna calls. A provider identity mismatch also disables later calls. Never substitute or change model/effort automatically.
- Role 3 owns requirements/audit/accounting and Role 4 owns checks/report/retry/ledger request. Preserve session/phase state over Stop continuations and duplicate events: at most two calls, one application repair, one separate ledger bookkeeping request. Never inherit old configurable retry defaults.

## Deliverables

- D-1, 10/28–11/03 after approval: SessionStart pin-check and advisory, verified-version evidence, exact artifact lifecycle and previously validated ledger injection. Revalidate identifiers/hashes against current workspace, never trust executor validation fields.
- D-2, 10/28–11/03: connect requirements and completion/report producers without contract approval machinery; show unanswered questions before work and record user answers. Coordinate prepared noninteractive clarifications with Role 5; never assume answers.
- D-3, by 11/03: escalation advice in completion report on repeated deterministic failure, recommending higher effort or human review without changing effort. Optional protected-file guard only after installed-version PreToolUse evidence; deterministic hash checks remain required even without the guard.
- D-4, before full runs: installer/check/packaging and two live smoke projects outside every evaluation set; exercise real hooks under codex exec, one repair, ledger writing and next-session injection. Keep process shutdown/capture evidence and artifact hashes.
- D-5, by 11/13: packaged demo and screen-order scenario for visible requirements, failure evidence and two-session ledger; support fresh-clone docs and rehearsal.

## Skill instructions for the executor

1. Show the numbered requirements table and open questions before work. Ask the user rather than inventing answers; no old generated-contract approval gate.
2. Follow exact named/protected files and configured checks. Provide a per-requirement completion table with command/output or path/hash evidence; items lacking an oracle remain unverifiable.
3. Handle only the executed failures in the single repair continuation. Audit opinions/unverifiable rows do not authorize extra repair.
4. When the separate Stop ledger request arrives, write schema-shaped decisions/rationale/fixed identifiers/open items with validation=null. Do not alter application code in that bookkeeping continuation. Preserve the application completion summary/evidence in the retained final response; do not replace it with only a ledger-save notice.
5. If pin-check disables Luna, show the advisory; continue ordinary work without claiming H3 validation or substituting a model.

## Success criteria

- SC-1: mocked hook stdin/stdout tests cover enabled/disabled pin, model/version/pricing failures, duplicate events, nullable transcript and exact nested guard before every side effect.
- SC-2: ledger schema/identifier/hash rejection prevents stale injection; pin failure produces no Luna calls.
- SC-3: one repair only on deterministic failure; one ledger request at most; no repeated audit/model call or recursive Stop block.
- SC-4: errors never strand a Codex session; retain visible advisory/evidence and allow exit when repair/bookkeeping budgets expire. Normal error/timing output must not violate the nested zero-byte guard.
- SC-5: hook-only overhead target under one second excluding command/model time; each Luna call target below 10 seconds, measured by Role 3.
- SC-6: install --check distinguishes unverified CLI, missing registration/skill, missing model and missing pricing; full smoke evidence establishes actual behavior rather than registry membership alone.

## Verification

Run `.venv/bin/python -m pytest tests/plugin -q`. Run installer --check and real
smokes only where authorized and available, retaining logs/version/model/tier
and hashes. No live batch of ten or more without estimate and STOP-3 handling.
Update STATUS; never claim live acceptance from mocked tests.

## Stop and escalate conditions

- STOP-P1: measured hooks cannot provide required continuation/context; propose an alternative without silently replacing real-plugin evaluation.
- STOP-P2: CLI changes mid-run; stop/report. Probe a new version and require one-task audit smoke before large runs per decision 0006.
- STOP-P3: measured Luna call exceeds the 10-second target; report evidence and a bounded design proposal. Do not switch model or add background calls automatically.

## First task

Read the frozen schema status and current STATUS. Implement D-1 now with mocked
pin/ledger/guard cases and the approved question-pause policy. Send evidence/proposals to owners without editing their paths.

## Assumptions

- PreToolUse is optional until measured compatible; a disabled pin disables Luna functionality, not the ordinary executor session.
