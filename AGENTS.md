# LocalHarnessMaker - Shared Working Rules

This file lives at the repository root. Every Codex session reads it automatically. Role-specific instructions live in the prompts/ directory. Identifiers used across all prompts: Role 1 to Role 5 for roles, D-n for deliverables, SC-n for success criteria, STOP-n for stop conditions.

## 1. Project summary

LocalHarnessMaker now builds hooks that compensate gpt-6.1-sol's measured
weaknesses with deterministic checks and two pinned gpt-6-luna calls per
completed session at low effort. Decision 0011 was accepted on 2026-10-25;
the interface version 3 schema set was approved by the user on 2026-10-25 at 01:55 KST and is frozen.

The first-prompt hook shows a requirements table and asks unresolved questions.
Stop runs deterministic checks, audits final-message claims with Luna, allows
one repair only on executed check failure, and asks the executor to write a
decision ledger. SessionStart validates and injects that ledger. No llm_judge
runs on this hook path. The old contract harness and v1/v2 reports are history;
the original cost-per-pass claim is answered negatively by those measurements.
H3 is evaluated only on a held-out version 3 set against A (Sol medium alone).
B is dropped for version 3, C optional, decision 0010 record-only.

Dates: development ends 2026-11-13. Final presentation 2026-11-16. The original
design is the Notion page "AI Project: GPT Operating Harness"; current direction
is docs/decisions/0011-pinned-luna-hook-direction.md and docs/plan.md.

## 2. Repository layout and ownership

| Path | Owner | Contents |
|---|---|---|
| AGENTS.md, docs/, prompts/, schemas/, root configuration | Role 1 Tech Lead | shared rules, design and decision records (docs/decisions/), schemas, pyproject.toml, Makefile, CI |
| plugin/ | Role 2 Plugin Engineer | hook configuration, hook scripts, skill, AGENTS.md template for user projects, install script |
| controller/ | Role 3 Controller Engineer | requirements-table and claim-audit prompts/calibration, pinned Luna client and accounting; historical generators retained |
| verifier/ | Role 4 Verifier Engineer | deterministic check runner, completion report, single-retry rule, Stop ledger request and mechanical validation |
| eval/ | Role 5 Evaluation Engineer | held-out version 3 tasks, plugin-mode runner, A/H3 configs, estimates, metrics and reports |
| state/STATUS-ROLE.md | each role | per-role status file used as the handoff between sessions |
| tests/ROLE/ | each role | unit and integration tests |

Rules:
1. Edit only the paths you own. Read everything else.
2. If you need a change outside your paths, write a proposal file in docs/decisions/ and stop.
3. Do not spawn sub-agents. One session per role.

## 3. Interfaces between roles

### 3.0 Frozen hook interfaces, version 3

Status: frozen, approved by the user on 2026-10-25 at 01:55 KST, exactly as proposed in
`docs/interfaces-v3.md` and `schemas/` at commit `d82b87a`.
`schemas/VERSION` stays 3 and now denotes the frozen set. Roles 2–5 start
implementation now. Any later change to a frozen v3 schema requires a new
decision, explicit user approval and a version increment. Publication does not
assert runtime implementation or compatibility.

Source of truth for frozen paths, mappings and sequencing:
[docs/interfaces-v3.md](docs/interfaces-v3.md), plus these closed draft 2020-12
schemas and examples in schemas/examples/:

| Schema | Required content |
| --- | --- |
| requirements.schema.json | Native session ID, prompt path/hash, state; numbered id/text/kind/source_excerpt/code-derived check rows; open_questions with nullable user answers; Luna accounting reference |
| completion-report.schema.json | Requirements hash; current final-message hash; per-requirement pass/fail/unverifiable and check evidence (output excerpt, path, hash); claim audit with cited evidence and audited-message hash; single-retry record; escalation advice |
| ledger.schema.json | Executor-written decisions/rationale and fixed names/signatures/constants with paths; open items; hook-owned validation with identifier presence and workspace hashes |
| pin-check.schema.json | Installed version, exact model-list/pricing checks with evidence hashes, enabled/disabled status, reason codes and visible advisory |
| luna-call.schema.json | One accounting JSONL line: session/call/phase, requested and actual model, backend, low effort, tokens, latency, pricing_ref, nullable USD, status/error |

Requirement kinds map deterministically: behavior -> configured project tests
or unavailable; constraint -> configured command/signature snapshot/input
immutability probe or unavailable; protected_file -> baseline hash unchanged;
named_file -> existence; named_command/test_command -> safe argv from the exact
request or configured project command. Unsupported/missing oracles are
unavailable/unverifiable. Luna never writes commands, regexes, paths or hashes.
Questions are shown before work; the user answers visibly. Never assume an
answer. No `llm_judge` on the hook path; historical schemas retain it.

Exact workspace artifact root: `.localharness/v3/`. Per-session directory:
`sessions/<sha256-of-UTF-8-session_id>/`, containing `pin-check.json`,
`requirements.json`, `claim-audit.json` (claim-audit block sidecar),
`completion-report.json`, `ledger.json`, `luna-calls.jsonl`
and referenced immutable `evidence/` files. `.localharness/v3/latest-ledger.json`
is an atomic copy of the last validated ledger and is revalidated on injection.
The ledger supersedes handoff only for this hook path; keep handoff.schema.json
for retained v1/v2 artifacts. All artifact paths are confined relative paths;
code checks IDs, source/target correspondence, hashes and call references.

Pin `gpt-6-luna` at low effort, verify installed Codex version/model list and
pinned pricing at SessionStart. Fail closed: missing/renamed/unobservable model,
unverified version, missing price coverage or provider identity mismatch writes
a visible advisory and disables Luna hooks; never silently substitute. At most
two calls per native session, one requirements and one claim audit, counting
failed invocations. No automatic retry/regeneration/fallback on this hook path.
Keep nullable unknown usage/cost; code records every call with pinned
API-equivalent prices. Target each call under 10 seconds and control cost well
under 2 percent of Fast executor cost; these are unmeasured targets.

Stop permits at most one application repair, only for an executed deterministic
failure. Unverifiable checks and claim-audit opinions never trigger repair.
After repair recheck with code, preserve the original audit and mark it stale
if the final message changed. Repeated failure yields advice, never an automatic
effort change. After the report settles, request executor ledger writing through
one separate Stop bookkeeping continuation; it does not extend repair or loop
on invalid ledgers. Hook code validates before save/injection.

Runner plugin mode launches Codex with the installed hooks and only collects
these artifacts for control/check/accounting results; it does not orchestrate
control calls or verification. A bypasses hooks with HARNESS_NESTED=1; H3 removes
that variable from copied executor/resume environments to run the hooks.
Controller-owned nested Codex children always set HARNESS_NESTED=1. Preserve
the immediate zero-byte guard below. Invalid pin/artifacts/accounting cannot be
presented as successful H3. Existing access audit/post-exit private grading
rules remain in force.

Success: H3 pass rate matches A within the paired interval, task-level false
done at least halved, cost per pass at most 15 percent above A; any quality loss
fails. Report paired uncertainty; no numeric equivalence margin is invented.
V1/v2 informed this design, so H3 is evaluated on v3 only. Historical report
schemas are retained unchanged; schema version and task-set version differ.

Section 3.1 describes retained v1/v2 schemas. Section 3.2 lists both historical
and frozen v3 CLIs. Section 3.3 maps v3 events onto measured wire channels and
retains the nested guard; section 3.4 applies to all evaluations.

Version 1 was approved and published on 2026-10-21, ahead of the planned
2026-10-24 freeze. Approved records: docs/decisions/0002-judgment-schema-proposal.md,
0003-evaluation-report-schema-proposal.md, and
0004-codex-cli-backend-and-nested-guard-proposal.md. Only Role 1 changes shared
interfaces. Later revisions require user approval, a decision record and an
increment of schemas/VERSION. Publishing an interface is not proof that its
owning role has implemented or measured it.

Version 2 was approved by the user and published on 2026-10-23 under
docs/decisions/0009-task-level-false-done.md. It adds the required evaluation
metric task_false_done_rate and sample unit claimed_complete_task; the historical schemas/VERSION
marker was 2. Both numerator and denominator use valid tasks only. Version 1 reports
remain valid version 1 documents; compare versions only with tools accepting both.

### 3.1 Historical schemas (directory schemas/, JSON Schema draft 2020-12)

All objects reject unknown fields. make validate-schemas checks all historical and frozen v3 schemas
and every reference example offline, including date/time formats and local
references. The schema files are the exact field/type definitions.

File contract.schema.json, the contract:
- task_summary: string
- constraints: array of string
- success_criteria: array of objects with id, description, check
  - check.type is exactly one of command, file_exists, regex, llm_judge
  - command uses command and expected; file_exists uses path; regex uses path and pattern; llm_judge uses rubric
  - expected has required integer exit_code and optional exact stdout, including newlines
- verification: array of objects with command and expected
- stop_conditions: array of string
- assumptions: array of string; the user corrects unspecified assumptions before approval
- reasoning_effort: value and rationale; value is low, medium, high, xhigh or max, computed in controller/analyze.py, never by the model
- cost_estimate: input_tokens, output_tokens, usd, computed by code

File verdict.schema.json, the verdict:
- items: array of objects with id, status, evidence, reason; status is pass, fail or unverifiable
- overall: pass or fail; pass requires all items to pass
- reinstruct_message: string of at most 300 characters or null; null on overall pass or retry exhaustion
- attempt: integer starting at 1

File handoff.schema.json, the handoff:
- done: array of objects with criterion_id and artifact
- remaining: array of objects with criterion_id and state
- decisions: array of objects with what and why
- verify_commands, do_not_touch: arrays of string

File judgment-input.schema.json, judge input:
- Exactly one full success_criteria item: id, description, check, without a list or contract wrapper.
- References the existing contract criterion definition and requires check.type=llm_judge. Mechanical criteria are input errors before any model call.

File judgment.schema.json, judge output:
- Exactly criterion_id, status, reason, evidence, model, usage.
- status uses the verdict vocabulary: pass, fail, unverifiable. criterion_id must match input id, and evidence must include llm_judge; runtime code enforces these relationships.
- Code supplies criterion_id, selected model identity and usage; generated content supplies status/reason/evidence only. Conflicting provider model identity is an error.
- usage has input_tokens, cached_input_tokens, output_tokens, usd, latency_seconds, cost_basis and pricing_ref. cost_basis is api_equivalent_usd. Unknown token counts/cost or missing price reference use null, never a fabricated zero. Cache tokens are a subset of input tokens.
- Sum all generation/regeneration/fallback usage and cost. Private per-call logs retain actual model/backend/pricing for mixed-model calls. Do not count billed reasoning tokens twice.

File evaluation-report.schema.json, eval/reports/NAME/report.json:
- metadata records run/config/task-set identity, hashes, Codex version, executor model/effort, control backend/model, seed, retry limit, pinned API-equivalent pricing, bootstrap configuration and optional hash-pinned parity comparator.
- tasks records task identity/type, two-session flag, outcome, invalid reasons, executor segments and their --json logs/hashes, grader_access_audit, trusted grading, handoff evidence, done claims, calls, costs and artifact references.
- grader_access_audit uses method=access_audit and status=clean, access_detected or inconclusive. Detected or incomplete audits require outcome=invalid, nonempty reasons and no grading result. Any invalid task makes aggregate validity=invalid; remaining quality metrics are diagnostic only.
- metrics contains exactly pass_rate, false_done_rate, task_false_done_rate, cost_per_pass, avg_attempts, handoff_success and parity. task_false_done_rate is false done valid tasks / claimed-complete valid tasks, with sample_unit=claimed_complete_task; tasks without a retained final message are undefined and excluded with a reason. Every metric has value, sample_size, sample_unit, ci95 and undefined_reason. ci95 has level=0.95, lower, upper and method=task_cluster_percentile_bootstrap.
- Use seeded task-cluster percentile bootstrap, default 10000 and minimum 1000 resamples; use paired tasks for parity. Zero original/bootstrap denominators or missing required accounting yield null value/bounds and a reason. Preserve local-minus-cheap_api parity; compare identical task sets/seeds/executor settings/Codex versions.
- accounting records attempted/valid/invalid task counts and total_cost_usd. Invalid tasks are excluded from quality samples, but their costs remain in total cost and cost_per_pass. Audit-clean failures/timeouts/errors remain valid quality samples.
- All costs are API-equivalent USD from a versioned per-model price snapshot, including CLI/local calls, failed calls, retries and fallbacks. Unknown usage/pricing stays null; a logged-in subscription is not free usage. Sum executor and all control calls once.

The existing contract/verdict/handoff shapes are unchanged in version 1.
Cross-artifact ID equality, counts, costs, CI ordering, observed model/effort,
process/copy ordering and other arithmetic require runtime checks in addition
to JSON Schema. Decision 0003 specifies metric units and runtime invariants.

### 3.2 Command line interfaces

#### Historical versions 1 and 2 (unchanged)

1. python -m controller contract --prompt FILE --handoff FILE_OR_none --cases DIR --backend codex_cli_OR_cheap_api_OR_local --out contract.json
2. python -m controller handoff --transcript PATH --contract contract.json --verdict verdict.json --backend codex_cli_OR_cheap_api_OR_local --out handoff.json
3. python -m controller judge --criterion JSON_FILE --artifact PATH --backend codex_cli_OR_cheap_api_OR_local --out judgment.json
4. python -m verifier check --contract contract.json --workspace DIR --transcript PATH --attempt N --out verdict.json
5. python -m verifier validate-handoff --handoff handoff.json
6. python -m eval run --config YAML --out eval/reports/NAME/

Backend is required and accepts exactly codex_cli, cheap_api or local. Primary
workflow/config selects codex_cli using gpt-6-luna through the existing CLI
login. cheap_api uses the same gpt-6-luna through HTTP Responses API with an
environment API key. Local Gemma 4 12B implementation and measurement are
dropped by decision 0007; the local selector remains unchanged and is never a
hidden cloud fallback. Names, endpoints, executables and deadlines are configurable.
Do not copy auth.json or derive HTTP credentials from the CLI login.

For codex_cli, transport unavailability/failure/deadline expiry may transition
once to cheap_api if its key and the remaining budget exist. A fail/unverifiable
judgment does not trigger fallback. There are at most three generation calls
per command total, across initial call, retries, fallback and regeneration.
Fallback consumes a slot and subsequent retries stay HTTP. No credential or
remaining slot means explicit internal error. Local unavailability is explicit.

Read CLI --json events as logs/accounting and final structured output from
--output-last-message. Use --output-schema with the strict adapter supported
by the installed CLI and validate locally before overwriting code-owned fields.
Subprocesses are injectable, use shell=False, piped input and bounded deadlines.

Conventions for every historical command:
- Exit 0 means successful computation, 1 input error, 2 internal error. Input validation occurs before model calls. A fail/unverifiable judgment or recorded invalid evaluation task is a successful computation, not a CLI error.
- Successful stdout contains exactly one output path plus a newline. Logs go to stderr; no success path is printed on error.
- controller/verifier outputs validate against their named schemas. eval prints its --out directory, containing report.json validated by evaluation-report.schema.json.
- validate-handoff validates without rewriting input and prints the supplied handoff path; no --out flag is added.

#### Frozen version 3 hook operations

Role 2 hooks are the only production callers. The evaluation runner never calls
these operations directly; it launches the installed hooks and collects artifacts.
The historical conventions above apply only to versions 1 and 2. The following
arguments, results and exit codes are the frozen v3 interfaces. `DIR` supplied to
`--artifacts` is the exact session artifact directory from section 3.0. All artifact
inputs/outputs below are inside it unless explicitly stated. Request/configuration
sources and the workspace are external inputs; hooks retain immutable prompt and
final-message snapshots under `evidence/` for the FILE arguments and hashes.
Inputs are validated before model calls. Command-specific exit codes and stdout
are specified below; historical stdout/exit conventions are not implicitly inherited.

| Operation and exact arguments | Reads and writes | Exit / stdout |
| --- | --- | --- |
| `python -m controller requirements --prompt FILE --session-id ID --artifacts DIR [--config FILE]` | Reads retained prompt FILE, optional external project config FILE, `pin-check.json` and phase accounting. One `gpt-6-luna` low call when enabled; writes `requirements.json` and appends one `luna-calls.jsonl` record per invocation. Luna supplies classification, text, source excerpts and open questions; code derives every check from request/configuration, never from Luna. | 0: schema-valid table, state `ready` or `pending_questions`. 2: pin/call failure, table state `unavailable`, visible advisory. A disabled pin invokes no model and appends no fictitious call record. |
| `python -m controller claim-audit --requirements FILE --final-message FILE --session-id ID --artifacts DIR` | Reads requirements FILE, retained final-message FILE, `pin-check.json`, phase accounting and cited evidence. One `gpt-6-luna` low call when enabled; writes the `claim_audit` block itself to `claim-audit.json` for verifier merge, and appends one accounting record per invocation. Sidecar validates against `completion-report.schema.json#/properties/claim_audit`; no new schema/envelope. | 0: schema-valid completed audit. 2: pin/call failure, sidecar status `unavailable`, visible advisory; no fictitious accounting for a disabled pin. |
| `python -m verifier check --requirements FILE --workspace DIR --session-id ID --artifacts DIR --round N [--claim-audit FILE] [--final-message FILE]` | Reads requirements FILE, external workspace DIR, optional audit sidecar and final-message snapshot, and prior report/retry state on recheck. Runs every row's deterministic check with `shell=False`, bounded deadlines and workspace isolation. Writes `completion-report.json` (`check_round=N`, N=1 or 2) and immutable `evidence/` files; merges supplied audit. Round 1 writes retry state and failing row IDs, recording whether one repair is warranted; persist `retry.used=1` before blocking for that repair. No extra report fields are added. | 0 whenever report written, whatever verdicts; stdout one-line JSON `{overall, failed_rows, unverifiable_rows, retry_warranted}`. `overall` is pass only if every row passes with ready requirements; otherwise fail. Row lists contain requirement IDs; `retry_warranted` is boolean, true only for executed deterministic failure with the repair available. 2: internal error. |
| `python -m verifier ledger-validate --ledger FILE --workspace DIR --session-id ID --artifacts DIR` | Reads ledger FILE and external workspace DIR; fills hook-owned `validation` in `ledger.json`. Atomically copies a valid ledger to `<workspace>/.localharness/v3/latest-ledger.json` (the sole output outside session artifacts); invalid ledger is not copied. | 0 valid; 1 invalid, advisory text on stdout; 2 internal error. |
| `python -m plugin.pin_check --session-id ID --artifacts DIR --codex PATH` | Reads external installed Codex executable PATH, verified-version/model/pricing configuration and observed evidence. Writes `pin-check.json` and referenced immutable `evidence/` snapshots. | 0 enabled; 1 disabled, advisory on stdout; 2 internal error. |

No automatic retry, regeneration or fallback is permitted. Every actual failed
invocation consumes its phase slot and is accounted once; pre-call pin failures
consume no provider invocation. Missing usage/cost remains null. Controller call
failures publish unavailable artifacts rather than inferred requirements/audits.

### 3.3 Hook input, output and nested environment guard

Source of truth for measured v1/v2 wire behavior: docs/hooks-contract.md,
published from Role 2's measured draft. Frozen v3 semantics in section 3.0
replace contract/handoff content on the same measured context/Stop channels;
they do not claim new production compatibility evidence.
It records the versions verified so far, starting with codex-cli
0.162.0-alpha.17.2 startup under interactive CLI and exec. Newer versions
require a hook compatibility probe first; see docs/decisions/0006-codex-version-policy.md.
Production behavior must be tested separately; startup evidence does not prove
the new guard, handoff, persisted trust or production retry limits.

- Common stdin fields: session_id, transcript_path (string or null), cwd, hook_event_name, model; UserPromptSubmit also has prompt. Additional event fields may be present, and transcript format is not stable.
- Historical UserPromptSubmit injects contract text through hookSpecificOutput.additionalContext with hookEventName=UserPromptSubmit.
- Stop continues unmet work with {"decision":"block","reason":"REINSTRUCTION"}; pass/retry exhaustion permits completion. The measured continuation does not fire UserPromptSubmit again, so preserve contract state. Do not block with a null re-instruction.
- Historical SessionStart injects validated handoff text through hookSpecificOutput.additionalContext with hookEventName=SessionStart.
- SessionEnd is observe-only. Do not use it.

Frozen v3 event mapping (no new hook wire fields):

| Event | Ordered behavior |
| --- | --- |
| SessionStart | Run pin-check, then mechanically revalidate and inject the latest ledger via `hookSpecificOutput.additionalContext`; show pin/ledger advisories. |
| UserPromptSubmit, first prompt only | Run requirements, show the table/questions, then inject: "if the requirements table has open questions, ask them and end the turn before changing any file". Record visible answers without another Luna call. |
| PreToolUse | Protected-file guard only if the installed Codex hook contract exposes a pre-tool event and compatibility is verified; otherwise defer the guard with a visible note. Do not invent an event or wire field. |
| Stop | If questions are pending and the workspace is unchanged, permit termination without a claim audit or ledger turn. Otherwise run verifier check and the claim audit at the first Stop only, merge/publish the report, block once for application repair only when `retry_warranted`, then recheck without another audit. After checks settle, request ledger continuation once, validate, then allow termination. Preserve the original audit and mark stale if the final message changes. |

The question pause applies to noninteractive sessions too. Silence is no answer;
Role 5 supplies prepared clarification visibly or marks an unresolvable run
invalid. Pending-question termination is a pause, not successful task completion.
It may omit later artifacts; do not require an audit/ledger merely to exit that
unchanged pause. This exception precedes the ordinary first-Stop sequencing.

HARNESS_NESTED=1 makes every LocalHarnessMaker hook exit 0 immediately with zero
bytes on stdout AND stderr. Compare the exact string "1" before reading stdin,
loading state/config, importing controller/verifier, logging timing, creating
files or calling any model/subprocess. Empty output is neither {} nor a newline.
Unset, empty, "0", "true" and "01" take the normal path. This guard precedes
normal handling and whole-script exception handling, including stub mode.

Set the guard in a copied child environment for every controller-owned Codex
subprocess/retry/resume and wrapper that can launch Codex. Role 5 sets it on
legacy runner-owned executor/resume processes and baseline A. H3
plugin mode removes it from copied executor/resume environments so hooks run;
H3 does not own an independent control loop. Do not
mutate the parent environment or persistent configuration. Normal direct-user
sessions leave it unset. Other plugins' hooks need separate verification.

### 3.4 Private grading and STOP-E4 access audit

The user-approved access audit supersedes decision 0001's deny-read prerequisite.
Private graders live outside the repository and all public executor workspaces.
Only after codex exec and spawned work exit, copy the public artifact into a
fresh trusted grading copy and copy in graders. Never run or resume Codex in a
grading copy, expose it to later executor turns, or return private test contents
to controller/executor context. Later attempts use only public workspaces and
fresh post-exit grading copies.

Retain and audit every --json execution/retry/resume stream and its SHA-256.
Inspect tool arguments/results for private source/copy paths and canonical
aliases, including children, traversal, listing/search/execution and denied
access attempts. Log matches with file, line, tool, path, operation and evidence.
Any observed private-grader access invalidates the task and aggregate report.
Missing/malformed/truncated/unsupported streams or unresolved operands invalidate
the audit as inconclusive. Assistant prose mentioning a path alone is not access.
A clean audit states no access was observed; it does not prove read isolation.

## 4. Working rules

1. Start of session: read the current state block and latest dated job section in state/STATUS-ROLE.md for your role. Continue from its first Remaining item, following History references when present. If the file is empty, do the First task section of your role prompt.
2. Assumptions: never guess. List anything the request does not specify under a heading named Assumptions, both in the PR description and in the STATUS file.
3. Bias to action: do not stop to ask questions. Produce a reviewable result, then report it together with your assumptions. Stop only for the conditions in section 5.
4. Definition of done: tests pass, STATUS file updated, change summary written. Every claim of done must carry evidence, meaning the command you ran and its output. Items without evidence are reported as not done.
5. End of session: update state/STATUS-ROLE.md using the format in section 6.
6. Tests: run only the tests of the package you changed. Run the full suite once before merge. Do not run the full suite after every small edit.
7. Code: Python 3.11 or newer, type hints everywhere. Comments, docstrings and commit messages in English. Conventional Commits with prefixes feat, fix, test, docs. pytest for tests. Every external call (HTTP API, model server, codex exec) must be mockable.
8. Scope: no unrequested refactoring or features. Do not change schemas, CLIs or hook interfaces. Only Role 1 may.
9. Secrets: API keys come from environment variables only. Never write them into the repository.
10. Reports: short paragraphs and tables. No decorative formatting, no repetition, no closing summaries.
11. Parallel jobs: different roles may work concurrently in their own worktrees. Within one role, concurrent jobs must use disjoint paths and unique job IDs, followed by a single consolidation job that integrates their changes, refreshes the STATUS current state block and runs the package checks. Append each job's dated STATUS section without rewriting another job's lines. This rule permits separate jobs, not sub-agents within a session.

## 5. Stop and escalate conditions

Stop and report to the user when any of these holds:
- STOP-1: progress requires changing an interface (schema, CLI, hook input or output).
- STOP-2: progress requires editing a path owned by another role.
- STOP-3: you are about to run 10 or more paid calls (executor model or control API) in one batch. Report the cost estimate first.
- STOP-4: the action deletes files, rewrites git history, or changes an external service configuration.

## 6. STATUS file format

File: state/STATUS-ROLE.md. Keep a short `## Current state` block at the top,
at most 10 lines including its heading. Only the single consolidation job
refreshes that block; ordinary jobs append their own sections at EOF.

Each job appends one section with the fixed header line
`## <date> <job id> <role>`, where date is YYYY-MM-DD in Asia/Seoul, job id is
unique within the role, and role is `Role 1` through `Role 5`. Completed job
sections are append-only: corrections and follow-up evidence belong in a new
dated section. Concurrent same-role jobs reserve disjoint implementation paths;
their STATUS appends are combined by the consolidation job without editing
the appended text. Archive pre-conversion prose under `## History`, preserving
all content and demoting its headings so the archive remains one section.
Do not infer dates or job IDs for legacy work; the conversion job's date labels
only the format migration. Historical completion claims retain their original evidence.

Within each dated job section use exactly these markdown level-3 headings, in order:

1. Done. One bullet per item, each ending with the evidence in parentheses: the command and its result.
2. Remaining. One bullet per item, in the order they should be done; carry forward or reference unresolved prior work explicitly.
3. Decisions. One bullet per decision in the form: what was decided, then a colon, then why.
4. Verify commands. One bullet per command that shows the current state is correct.
5. Do not touch. One bullet per path or rule the next session must not change.
6. Assumptions. One bullet per assumption made during the session.
