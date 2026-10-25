# Role 4: Verifier Engineer

Read AGENTS.md and state/STATUS-verifier.md first. Shared ownership, working
rules and STOP-1 through STOP-4 apply. Do not spawn sub-agents. Decision 0011
replaces old contract/judge/handoff deliverables for the new hook path.

## Goal

Publish per-requirement completion evidence using deterministic checks, permit
one repair only on executed failure, and request/validate the executor's own
decision ledger through Stop continuation. llm_judge is retired from this hook
path. Claim audit is supplied by Role 3; its opinions cannot override code.

## Ownership

verifier/, including check runner, claims extraction, report/retry logic,
ledger validation, command isolation and RULES.md; tests/verifier/ and
state/STATUS-verifier.md. Read other paths; never edit controller/, plugin/,
eval/, shared schemas or another role's STATUS.

## Interfaces

AGENTS.md section 3.0 and docs/interfaces-v3.md are the frozen v3 contract,
approved by the user 2026-10-25 at 01:55 KST from commit d82b87a; start implementation now.
Sections 3.2–3.3 freeze hook CLIs and event mapping, including question pause. Keep old verifier
check/validate-handoff CLIs and historical schemas compatible; do not extend
CLIs beyond the frozen v3 operations without a separately approved proposal. No judge CLI on the v3 hook path.
Use requirements.json, completion-report.json, ledger.json and immutable
evidence/ under `.localharness/v3/sessions/<sha256-of-UTF-8-session_id>/`.
Role 3 supplies the one audited claim result/accounting, via package integration
coordinated with Role 2; verifier must not import controller or invoke another
control call itself. Code checks cross-artifact IDs, hashes and provenance.

## Deterministic rules and Stop sequence

1. Code derives checks from exact request targets/configured project oracles, coordinated with Role 3. behavior: configured tests or unavailable; constraint: configured command/signature snapshot/input-immutability probe or unavailable; protected_file: pre-edit SHA-256 unchanged; named_file: existence; named/test_command: trusted safe argv. No model-generated regex/command or llm_judge. Unsupported derivation remains unverifiable.
2. Commands use bounded deadlines, shell=False, no network/outside writes and injected runners. Compare observed result to explicit expected exit, retaining argv, exit and output. Capture full output/hash plus bounded report excerpt. Preserve deterministic failures versus unavailable dependencies/timeouts/errors; missing named output/hash mismatch is fail. Record language-aware signature/input baseline evidence before edits.
3. Every requirement appears once with pass/fail/unverifiable, reason, file/output path and hash/excerpt. Passing tests do not establish uncovered behavior; no overall pass with unavailable rows. Validate cited claim evidence; unsupported claim citations cannot change deterministic status. Keep last-session final-message extraction rules available to Role 5.
4. At first Stop run checks and publish report with Role 3's one audit. Only an executed deterministic failure permits one application repair. Persist retry.used=1 and failed IDs before block; inject only those rows with concrete failure evidence. Unverifiable rows and claim opinions never trigger repair.
5. After repair recheck deterministically, publish round 2, no extra Luna call. Preserve original audited message/hash and mark audit stale if the current final message changed. Coordinate repeated-failure advice with Role 2; never raise effort automatically or block for a second repair.
6. After report settles, request ledger writing via one separate Stop bookkeeping continuation. Executor writes decisions/rationale/fixed names, signatures/constants/paths/open items and validation=null. This request is not application repair and cannot alter app code. Require the final response to preserve application completion claims/evidence, not only a ledger-save notice; refresh current-final-message hash/stale-audit status if it changes. Persist request state before block; duplicate Stop events cannot loop.
7. Hook code owns validation: schema, exact identifier coverage/presence, hashes, confined paths and current workspace identity. Unsupported extraction/missing identifiers -> invalid. Never trust executor-populated validation. Save validated latest-ledger for Role 2 injection, revalidate on next session; no Luna transcript reconstruction. Invalid/missing ledger is advisory, not another blocking continuation or silent older-memory injection.

## Deliverables

- D-1, 10/28–11/03 after approval: deterministic runner for code-derived checks, mechanical baselines, safe execution and complete per-row evidence; unavailable coverage stays explicit.
- D-2, by 11/03: completion-report producer, injected claim audit integration, strict single-retry state machine, stale audit handling, repeated-failure advice integration with Role 2. Retain claims extraction for task false done without adding judge work.
- D-3, by 11/03: Stop ledger writing request and mechanical schema/identifier/hash validation. Support two non-evaluation smoke projects and two-session ledger evidence with Role 2.
- D-4, by 11/13: RULES.md, independently sampled report-accuracy review support, fixes confined to development evidence before v3 freeze; document known unsupported checks and stale-audit limitation.

## Success criteria

- SC-1: each deterministic check has pass/fail/unverifiable cases with meaningful evidence; unsafe/unsupported commands never execute.
- SC-2: false completion fixture exposes failed checks despite executor saying done; unsupported claims do not become evidence or trigger repair alone.
- SC-3: verifier never imports controller; no llm_judge/provider calls on the new hook path.
- SC-4: state-machine fixtures prove only one application repair, at most one ledger request, duplicate Stop idempotence and no audit rerun. Unverifiable-only reports never repair.
- SC-5: forged ledger validation, identifiers absent/changed, stale hashes, path escapes and invalid schema block injection without repeated continuation.
- SC-6: deterministic report/check overhead target below one second excluding commands/model calls; measured separately from project tests.

## Verification

Run `.venv/bin/python -m pytest tests/verifier -q`; validate report/ledger fixtures
with local schema references and runtime cross-artifact checks. Host-only
sandbox/Codex tests need real evidence; mocked results are not live acceptance.
Update STATUS with exact commands/results and pending integration limits.

## Reporting

Final report at most 40 lines. Limit README and CHANGES edits to what changed.
Do not restate the brief. Append the dated job STATUS section required by
AGENTS.md section 6; only the consolidation job refreshes the current state block.

## Stop and escalate conditions

- STOP-V1: shared schema/CLI addition needed; propose it and stop before changing another role's paths.
- STOP-V2: installed transcript/Stop behavior differs from measured docs/hooks-contract.md; report evidence, never guess the format.
- STOP-V3: command isolation cannot block a dangerous operation; report and mark unverifiable rather than execute it.

## First task

Read frozen interface status and current STATUS. Implement deterministic failure versus
unverifiable and Stop-state fixtures; implement D-1 now under
the approved interfaces. Coordinate derivation/claim-adapter boundaries with Role 3 without
changing their files.

## Assumptions

- Ledger validation proves presence/identity, not the semantic quality of a decision. Report that limitation and preserve open items.
