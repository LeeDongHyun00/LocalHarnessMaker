# Hook interfaces, version 3

Status: frozen, approved by the user on 2026-10-25 at 01:55 KST, exactly as proposed at commit
`d82b87a` in this document and `schemas/`, under [0011](decisions/0011-pinned-luna-hook-direction.md).
`schemas/VERSION = 3` includes [amendment 0012](decisions/0012-pin-check-observed-service.md),
accepted by the user on 2026-10-25 at 05:55 KST. The set remains frozen at
version 3 with this approved exception to the version-increment rule. Only the
pin-check schema and its examples are amended; other frozen schema bytes
(including original proposal metadata) remain preserved. Any subsequent change
requires a new decision, explicit user approval and a version increment.
Versions 1/2 interfaces remain in [interfaces.md](interfaces.md), including all
six historical CLIs. Frozen v3 hook operations and event mapping are published
in [AGENTS.md sections 3.2–3.3](../AGENTS.md); no new hook wire fields are added.

## Artifact directory and collection contract

The sole root is `<workspace>/.localharness/v3/`. No Codex-home override is used.
The session directory is `sessions/<session_key>/`, where `session_key` is the
lowercase SHA-256 hex digest of the UTF-8 native `session_id`. Artifacts retain
the native ID; code verifies the directory/ID relationship. This avoids path
injection from session IDs. All paths below are exact relative to that directory.

| File | Schema / owner | Consumer |
| --- | --- | --- |
| `pin-check.json` | pin-check.schema.json / Role 2 | User, hook gate, runner |
| `requirements.json` | requirements.schema.json / Role 3 | User, checks, executor, runner |
| `claim-audit.json` | completion-report.schema.json#/properties/claim_audit / Role 3 | Role 4 merges into completion report; runner retains sidecar |
| `completion-report.json` | completion-report.schema.json / Role 4, claim audit by Role 3, advice by Role 2 | User, runner |
| `ledger.json` | ledger.schema.json / executor through Role 4 Stop continuation; validation by hook | Next session via Role 2, runner |
| `luna-calls.jsonl` | Each line validates with luna-call.schema.json / Role 3 | Runner accounting |
| `evidence/` | Exact bytes referenced by artifact/evidence objects / producing role | Hash checks and offline review |

Additionally `<workspace>/.localharness/v3/latest-ledger.json` is an atomic copy
of the last schema-valid, mechanically valid `ledger.json`, not a new envelope
or symlink. SessionStart checks it against the current workspace again before
injection. Never inject a stale/invalid ledger; publish a visible advisory.
A failed current ledger must not silently select an older ledger as current.
Select the most recent prior session by retained pin-check.checked_at, excluding
the current native session; require its session ID to match the latest copy.
Missing prior artifacts, timestamp ties or identity conflicts produce an
advisory and no injection, rather than a search for older usable memory.

JSON files are atomic replacements; JSONL is append-only UTF-8, one complete
object plus newline per actual provider invocation. Lock phase/call allocation
before invoking a provider; repeated hook events cannot duplicate calls.
Evidence snapshots are immutable and named by phase/round; reports reference
the bytes actually checked. Artifact paths are session-relative; requirement
check paths and ledger identifier paths are workspace-relative. Reject absolute
paths, `..` escapes and symlink escapes; resolve against the declared root.
Hashes are SHA-256 of retained bytes, lowercase 64-character hex. Do not accept
executor-written validation/accounting as trusted hook evidence.

The runner's new plugin mode launches `codex exec` with the plugin installed,
retains every execution/continuation log and hash, and after all executor and
child processes exit collects this entire root for every task/session, including
referenced evidence. It reads only these artifacts for hook/control results and
pricing, never calls contract/judge/handoff generators or the verifier to
orchestrate the hook loop, and never regenerates missing artifacts. It may
recompute prices from its pinned snapshot and must reconcile pricing references,
model identity, call counts and token totals. Hash-pin the collected files in
existing report artifact references; missing/malformed/inconsistent required
artifacts or pin-disabled H3 is invalid with reasons, never a zero-cost pass.
An interrupted session may lack later artifacts; retain partial files and costs.
A completed H3 session requires all five files; the unchanged pending-question
pause described below is exempt until work resumes (JSONL may be empty only if
Luna was disabled, which cannot establish a valid H3 result).

A uses no LocalHarnessMaker hooks and sets `HARNESS_NESTED=1` in a copied child
environment. H3 must explicitly remove that variable in its copied executor
and resume environments so hooks execute. Every controller-owned nested Codex
child still sets it to the exact string `1`. Never change the parent environment
or persistent configuration. Preserve native Stop continuations; the runner
does not launch its own repair loop. Any runner resume must retain hook state
and stay in the public workspace. Grading remains post-exit in a fresh trusted
copy; never resume an executor in a grading copy or expose private findings.

## Requirements and deterministic derivation

`requirements.schema.json` has session identity, prompt artifact/hash, state,
numbered requirements (`R-1`, `R-2`, ...), open questions and a Luna accounting
reference. Each row has id, number, text, kind, verbatim request source excerpt
and code-owned check. IDs are unique, numbers contiguous starting at 1, and IDs
match numbers. Code verifies source excerpts against retained request bytes;
Luna supplies classification/text/questions, never executable checks, paths,
regexes, expected values, hashes or accounting. Code extracts targets from the
original request/configuration and records unsupported derivations as unavailable.

| Kind | Code-derived check | Missing/ambiguous oracle |
| --- | --- | --- |
| behavior | `command` for explicitly configured project tests that cover the row | `unavailable`, reason required; tests alone do not prove every behavior |
| constraint | Configured `command`, `signature_snapshot` or `input_immutability` probe; baseline captured before edits | `unavailable`; never invent a probe from prose |
| protected_file | `file_unchanged` with pre-edit SHA-256 of explicitly named file | `unavailable` if absent/unreadable or target ambiguous |
| named_file | `file_exists` for exact request-named workspace path | `unavailable` if target cannot be safely resolved |
| named_command | `command`, argv from exact request command, expected exit code from request or configured zero-success convention | `unavailable` for unsafe/unsupported syntax |
| test_command | Same as named_command, or explicitly configured project test command | `unavailable` if no trusted command exists |

Commands use `shell=False`, bounded deadlines, captured exit/output and workspace
isolation; no network or outside writes. Code supports only safely parsed argv;
unsupported shell syntax is not rewritten by Luna. `cwd` is workspace-relative.
Signature checks use configured language-aware extraction and baseline hash;
input probes use configured argv and before/after hashes of declared fixtures.
A nonzero expected exit can be explicit. Exceptions, missing dependencies,
timeouts or unsupported check types are unverifiable; a completed check whose
observed result differs from its expectation is fail. Hash mismatch, missing
named output and changed signature are deterministic failures.

An unavailable check remains unverifiable in the report, even if Luna approves
a claim. Never route to `llm_judge`. Zero rows is not a passing requirements
table. `state=ready` requires at least one row and a successful referenced call.
Unanswered questions require `pending_questions`; present them before work and
wait for the user's visible answers. Code records answers without a new Luna
call or choosing an interpretation. In noninteractive runs, Role 5 must provide
a prepared clarification mechanism or mark the task invalid; silence is not an
answer. Pin/call failure produces `unavailable` with visible reason via the
advisory/accounting and no inferred requirements. The first-prompt phase occurs
once per native session, not again for clarification or Stop continuation.

The first-prompt hook injects the approved instruction: "if the requirements
table has open questions, ask them and end the turn before changing any file".
When questions are pending and the workspace is unchanged, Stop permits
termination without a claim audit or ledger turn. This is a clarification pause,
not a completed task, and adds no hook wire fields. Never treat silence as an
answer; prepared noninteractive clarification must still be visible.

## Completion, retry and ledger sequencing

`completion-report.schema.json` references the exact requirements snapshot and
current retained final message. Every row appears exactly once with pass, fail
or unverifiable, reason and evidence objects (`kind`, path, hash, excerpt).
Pass/fail require executed check evidence; excerpts reference full retained
outputs/files rather than substituting for them. Hook code supplies verdicts;
Luna's audit records which requirement the final message claims and the evidence
it cites, assessed supported/unsupported/unverifiable. The hook verifies cited
paths/hashes; invented citations are unsupported. Claim-audit opinions never
turn deterministic verdicts into pass or trigger repair. No overall pass is
inferred while any row is fail/unverifiable or the requirements are unavailable.

Except for the unchanged pending-question pause above, at first Stop, run checks, spend the one claim-audit call, and publish the report.
If any executed check fails, persist `retry.used=1` and its failed row IDs before
one `decision=block` repair continuation with concrete evidence for those rows
only. If none fails, do not repair. After the repair, recheck deterministically,
write round 2, and do not call Luna again. Keep the original audited message;
if the current final message changes, mark the audit stale, retaining its source
hash. Do not pretend the revised final message was audited. Null/missing final
message yields an unavailable audit and explicit reason. The report can be
updated during later Stop events without spending another call or repair.
Repeated executable failure produces escalation advice (higher effort or human
review); no automatic effort change. Unverifiable items may recommend human
review but never justify a repair. A failed Luna call is visible, not a reason
to spend another provider call.

After checks settle, Role 4 requests ledger writing from the executor via a
separate Stop continuation at most once. This bookkeeping continuation is not
the one repair and cannot repair application code. Persist its requested state
to prevent recursion. The executor writes decisions with rationale, fixed names,
signatures/constants and paths, plus open items. Executor output has
`validation=null`; hook code replaces that with measured validation, checking
every identifier using supported extraction and recording found flags and file
hashes. Unsupported extraction or missing/mismatched identifiers is invalid.
Validation must cover exactly the listed identifiers and referenced files;
`valid` requires all found and hashes to match the current workspace. It validates
presence/identity, not whether the decision was wise. An invalid/missing ledger
gets an advisory and is not injected; never keep blocking for ledger repair.
The bookkeeping request also instructs the executor to preserve its application
completion summary and evidence in the retained final response, rather than
replace them with only "ledger saved". Evaluation still classifies the retained
last-session final message identically for A and H3; a missing application claim
is not silently substituted with an earlier message. Refresh the report's
current-final-message hash and stale-audit status if bookkeeping changes that
message. Retain the application/ledger continuation distinction in evidence to
expose any claim-denominator effect. The hook then permits termination.
No SessionEnd generation is used.

`ledger.schema.json` supersedes handoff only for this hook path. The historical
handoff schema/examples and old CLIs remain unchanged for v1/v2 consumers.
Ledger validation is schema plus runtime ID/hash/path checks, not an LLM call.

## Pin advisory and call accounting

SessionStart writes `pin-check.json` before Luna work, with exact requested model
`gpt-6-luna`, observed CLI version, version/model/pricing checks, hash-pinned
model verification evidence and pricing snapshot, pricing_ref, reason codes and user-readable
advisory. `enabled` requires every check true and observed evidence. Missing,
renamed or unobservable model, unverified version, absent price coverage, or
conflicting provider model identity disables all later Luna calls. The user sees
why; the normal executor session may continue, but must not be represented as
H3. Deterministic guard/ledger behavior remains available if safely configured.
Do not substitute a newer model, use local control or derive HTTP credentials
from CLI login. Pin failure is fail-closed for Luna functionality, not permission
to change external configuration. Probe newer CLI versions before using them.

Amendment 0012 permits two model verification sources in `model_evidence`:
`listing` for an exact model-list entry, or `probe_observation` when no listing
facility answers. The object is optional for disabled results and required for
`enabled`, whose `reason_codes` stays empty. It has required fields `source`,
`observed_model` (string), `service_tier` (string or null), `observed_at` (RFC 3339),
`thread_id` (string or null), and `evidence_sha256` (64 lowercase hex or null).
The object rejects unknown fields. Listing verification records `source=listing`.
Existing `checks` and `model_list` schema constraints remain unchanged; the
synthetic probe example does not establish a real listing or live acceptance.

Host operator procedure when the installed CLI version changes:

1. Verify hook compatibility for that exact version under decision 0006. Try the
   supported listing facility; a responding list must contain the exact pin.
2. If no listing facility answers, run a minimal pinned `gpt-6-luna` probe at
   low effort and retain the native service identity evidence (for example,
   `thread_settings_applied`), observed tier, timestamp, thread ID and evidence
   hash. This is an operator action outside the two per-session hook calls;
   SessionStart does not automatically invoke a model probe.
3. Record that version's observation in `plugin/VERIFIED_VERSIONS.json` as
   `luna_observation`, then enable H3 only after pin, pricing and artifact
   validation pass. A version without recorded observation stays disabled;
   never reuse another CLI version's observation or fabricate missing fields.

The controller still checks requested model equals observed model on every
call. A mismatch records `pin_mismatch` and exits 2, rather than accepting the
output. Observed availability does not replace this enforcement or permit
fallback from an answering list that omits the pin. Registry/runtime changes
belong to the owning roles; this interface publication does not implement them.

At most two provider invocations per native session: one requirements and one
claim audit, each low effort. Failures, transport attempts, regenerations and
fallbacks consume calls; each phase has one slot, so v3 performs no automatic
fallback/retry. Primary `codex_cli`; explicit `cheap_api` is allowed only for the
same pinned model with an environment key and verified pin. The historical
three-call command budget is not inherited by hooks. Call results and output
validation failures are recorded even if no useful table/audit can be emitted.

Each JSONL record has native session ID, unique call_id, phase, backend,
requested_model, actual model (null if unobserved), low reasoning effort, status,
error, input/cached/output tokens, latency_seconds, usd, pricing_ref and
cost_basis=`api_equivalent_usd`. Code owns every field. A reported identity
mismatch is recorded as pin_mismatch with the actual identity, disables later
calls and is never accepted output. Unknown tokens/prices/cost remain null;
cached tokens are a subset of input and reasoning tokens are not double billed.
Record failed/timeout calls once and include them in total cost. Use a versioned
snapshot; the example pricing reference and hashes are synthetic, not real
rates. The runner sums executor and these provider calls once; it must not also
count nested controller usage as executor usage from duplicate logs.

Targets: each call below 10 seconds measured, combined control cost well under
2 percent of Fast executor cost. Missing evidence cannot establish a target.
The success criterion remains at most 15 percent extra cost per passing task
with quality preserved and task false done at least halved.

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

## Frozen hook event mapping

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

## Approval and validation

Affected roles: Role 1 publishes; Role 2 gates/injects/collects hook state; Role 3
produces requirements/audit/accounting; Role 4 runs checks/retry/ledger validation;
Role 5 collects artifacts and prices them without control orchestration.
JSON Schema validates shapes, closed fields, kind/check compatibility and basic
bounds. Owning-role runtime checks enforce unique IDs, source correspondence,
path confinement, hashes, call references/counts, pin/result identity, provenance,
question readiness, check verdicts and continuation order. Publication does not
claim these checks are implemented. Run `make validate-schemas` and
`.venv/bin/python -m pytest tests/lead -q` offline; historical fixtures stay valid.

## Assumptions

- This is the approved workspace-only artifact layout; no existing plugin state path is migrated by documentation.
- Code uses a configured zero-success command convention when the request gives no exit expectation; ambiguity about behavior remains a user question.
- One audit before repair preserves the two-call budget. A changed final message is explicitly stale; report-accuracy evaluation must retain that limitation.
- A ledger-only Stop continuation is separate from, and cannot extend, the single application repair. Its final response preserves the application outcome so bookkeeping does not erase completion claims. These sequencing choices are approved.
