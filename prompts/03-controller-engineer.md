# Role 3: Controller Engineer (pinned control model)

Read AGENTS.md and state/STATUS-controller.md first. Shared working rules,
ownership and STOP-1 through STOP-4 apply. Do not spawn sub-agents. Accepted
0011 supersedes contract generation, judge and transcript-handoff work items.

## Goal

Produce a useful requirements table and a grounded final-message claim audit
with two pinned gpt-6-luna calls per completed session at low effort. Keep
checks, identifiers, hashes, model identity, usage and cost code-owned. Luna
never invents executable checks or decides whether deterministic tests pass.

## Ownership

controller/, including client/backends, configuration/prices, controller/prompts/,
calibration fixtures and accounting; tests/controller/ and
state/STATUS-controller.md. Read everything else. Never inspect eval/tasks*,
private graders, retained evaluation implementations or reports to tune prompts.
Build independent calibration samples in tests/controller/fixtures/.
Do not edit verifier/, plugin/, eval/, root prompts/ or shared schemas.

## Interfaces

AGENTS.md section 3.0 and docs/interfaces-v3.md define the proposed v3 schema and
artifact set. Start implementation after explicit schema-set approval; prompt
and calibration design can be prepared now. Old contract/handoff/judge CLIs and
their codex_cli/cheap_api/local selectors remain compatible history, not new
hook deliverables. No new public CLI without a separate approved proposal.

1. Primary codex_cli, exact gpt-6-luna, reasoning effort low. SessionStart pin evidence is required before calls; provider model mismatch fails closed. Explicit cheap_api requires the same model, verified pin and environment key; never copy auth.json or derive HTTP credentials from CLI login. Local/automatic fallback is not used by hooks.
2. Hook budget: one requirements invocation and one claim-audit invocation per native session, at most two total including failure/timeout/malformed output. No automatic regeneration, retry or transport fallback. Legacy three-call command limits do not apply here. Lock phase allocation before provider invocation and keep it through Stop/clarification events.
3. Every controller-owned Codex child/retry/resume/wrapper gets HARNESS_NESTED=1 in a copied environment. Inject subprocess/HTTP clients, use shell=False, pipe input, bounded deadlines, --json for logs/accounting and --output-last-message for final structured output, locally validated. Do not mutate parent/persistent config.
4. Write requirements.json and append every actual call to luna-calls.jsonl in `.localharness/v3/sessions/<sha256-of-UTF-8-session_id>/`, retaining evidence. Code fills checks/accounting; Luna produces only row text/kind/source excerpts/questions or claims/citations. Verify excerpts against the original request. Code derives named targets/argv and baselines from request/configuration, coordinated with Role 4. No generated regex/command/path/hash is executable authority.
5. Open questions surface before work. Unanswered questions remain pending; code records visible user answers without another Luna call. Noninteractive silence is not confirmation. Missing oracle -> unavailable check -> unverifiable verdict, never a judge fallback.
6. Audit the retained executor final message against exact requirements. Record claimed requirement IDs, claim excerpts and cited evidence; verify paths/hashes with code. Claim opinion never triggers repair or overrides deterministic results. One audit before repair; if final message changes, retain the original audit with stale status, no new call. Do not reconstruct ledgers from transcripts.
7. Accounting: actual/requested model, low effort, backend, phase/call ID, success/error/timeout/pin_mismatch, nullable tokens/cache/output/cost, measured latency, versioned pricing_ref, cost_basis=api_equivalent_usd. Sum once, including failed calls. Unknown stays null; cache is an input subset and billed reasoning is not counted twice. Use pinned API-equivalent pricing, not subscription-free accounting.

## Deliverables

- D-1, 10/25–10/27: requirements-table and claim-audit prompt designs plus independent calibration sets. Include dense specs, ambiguous inputs, protected/named files/commands, nonexistent paths, unsupported shell syntax, adversarial request text and unsupported claims/citations. Keep calibration separate from every evaluation set.
- D-2, 10/28–11/03 after schema approval: pinned low-effort client, code-owned check derivation, question handling, two-phase budget, exact accounting artifacts and mocked golden tests. Retain injectable transport/deadline/nested guard infrastructure.
- D-3, by 11/03: calibrated schema/requirement/claim quality, ambiguity-question precision/recall and per-call latency/cost evidence on independent samples; support two non-evaluation hook smokes with Roles 2/4. Each call target below 10 seconds, control cost well under 2 percent of executor cost at Fast prices; report measured denominators and misses.
- D-4, by 11/13: stabilize integration without evaluation-driven tuning after v3 freeze; document limitations. Local Gemma, QLoRA, case-based contract generation, effort selection, judge and Luna-written handoff are not v3 work.

## Success criteria

- SC-1: valid fixtures and rejected malformed output prove code controls executable checks/usage/model identity; no LLM-authored command can reach execution.
- SC-2: ambiguous fixtures ask questions instead of assuming; record expected-question coverage and false questions with sample counts.
- SC-3: duplicate events, failed calls and malformed outputs cannot exceed two total or one per phase; pin failure makes zero calls. Mismatch is retained and disables later calls.
- SC-4: every actual provider call has one accounting line; unknown usage remains null and never fabricated zero. Deadlines and subprocesses are mockable.
- SC-5: wrapped untrusted request/artifact text cannot change output rules or turn citations into commands; forged evidence stays unsupported.
- SC-6: controller never imports verifier; independent prompt calibration never reads evaluation content.

## Verification

Run `.venv/bin/python -m pytest tests/controller -q`; validate produced fixtures
against the proposed/approved schemas with local references. Live independent
calibration/smokes only on an authorized host, with cost estimate before any
batch of ten or more. Update STATUS with exact outputs and pending targets.

## Stop and escalate conditions

- STOP-C1: additional shared field/CLI is required; write proposal and stop, without editing the interface.
- STOP-C2: required pinned model/output support is unavailable; report, never substitute or inherit legacy fallback retries.
- STOP-C3: plan to train on executor/paid-model output; report and await the existing terms review. Training is out of v3 scope.

## First task

Read schema approval status. Prepare prompt/calibration designs without touching
evaluation data; implement only once approved, starting with mocked budget,
accounting and code-owned derivation tests. Update STATUS-controller.md.

## Assumptions

- Raw model output is an internal adapter detail; public hook artifacts contain code-owned checks and verified accounting. Any required public interface extension follows STOP-C1.
