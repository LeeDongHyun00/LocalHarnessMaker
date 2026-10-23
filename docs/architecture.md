# Architecture

LocalHarnessMaker wraps a direct-user Codex session with a contract, evidence
checks and saved progress. Version 1 artifacts are defined in `schemas/`; the
[CLI interfaces](interfaces.md) and [hook contract](hooks-contract.md) define the
boundaries. This description follows the implementation and retained evidence;
the historical local-model design is superseded by
[decision 0007](decisions/0007-scope-cuts.md).

## Hooks and skill

| Component | Implemented responsibility |
|---|---|
| SessionStart | Validate the current `.harness/handoff.json` and inject `HARNESS_HANDOFF`; new sessions reset attempts, while a resumed session preserves its approval state. |
| UserPromptSubmit | Generate and validate a contract, inject `HARNESS_CONTRACT` with the skill instructions, wait for exact `approve`, and check the reviewed contract hash. Edits generate a new contract. |
| Stop | Verify approved work, block with a non-null re-instruction before the attempt limit, or save a validated handoff on pass/exhaustion. Exhaustion lists unmet IDs, reasons and evidence. |
| `plugin/skills/harness/SKILL.md` | Display goal, criteria, assumptions, effort and estimate before implementation; wait for approval; execute verification; report every criterion with evidence; address only re-instructed items. |

SessionEnd is observe-only and unused. Handoff saving happens at Stop, so an
abrupt session exit does not promise a newly saved handoff. Stop continuation
does not fire UserPromptSubmit again; it uses the existing approved contract.
State and private session metadata are atomically replaced in `.harness/`.
Malformed session metadata is archived and reset, with a warning.

Every hook first compares `HARNESS_NESTED` with the exact string `1`, exiting
with no stdout/stderr before stdin, imports, state or logging. Controller and
runner-owned Codex children receive this flag in copied environments. Normal
user sessions leave it unset. The project marker `.local-harness-maker` is
checked against canonical cwd ancestors before runtime work; unmarked projects
remain inactive. This guard does not establish behavior for other plugins.

Hook exceptions fail open: empty stdout, warning on stderr and exit 0. Missing
transcripts cannot support verification. The skill remains guidance rather than
an unconditional enforcement guarantee. In particular, a failed verdict with
null feedback before exhaustion is logged as a hook error, not blocked with a
null reason; the verifier's overall failure remains a failure.

## Controller

`controller contract`, `handoff` and `judge` are separate CLI operations. Their
inputs validate before model calls; structured outputs validate locally.
`controller/analyze.py` computes reasoning effort and code computes costs rather
than trusting generated values. The primary configuration is `codex_cli` with
`gpt-6-luna`, low control-model effort, read-only sandbox and existing CLI login.
It sends piped input with `shell=False`, uses `--output-schema`, reads final
structured content from `--output-last-message`, and retains `--json` events
for accounting.

On CLI transport failure/unavailability/deadline expiry, routing may transition
once to `cheap_api`, the HTTP Responses API with the same `gpt-6-luna`, only if
an environment API key and remaining call slot exist. Later calls stay HTTP.
Fail/unverifiable judgments do not cause fallback. All retries, regeneration
and fallback share at most three generation calls per command. No key or slot
means an explicit internal error. CLI auth is never converted to HTTP credentials.
The `local` selector remains for interface compatibility; local Gemma 4 12B and
QLoRA implementation/measurement were dropped. Local unavailability is explicit,
and parity remains not measured.

## Verifier

The verifier combines command, file-existence and regex checks with checklist
matching and done-claim evidence. Overall pass requires every item to pass;
`fail` and `unverifiable` remain distinct. Supported direct Python commands run
under macOS Seatbelt with network denied, sanitized environment, writes confined
to the canonical workspace and bounded process-group lifetime. Unsupported
commands, platforms or sandbox setup failures never run unsandboxed. The parser
rejects shell operators and escaping path operands. See
[verifier/RULES.md](../verifier/RULES.md) for the accepted command grammar.
Seatbelt does not establish read isolation or prevent every destructive action.

For `llm_judge`, the verifier launches `python -m controller judge` with exactly
one criterion and the artifact path. It does not import the controller. Returned
judgments are schema-validated and checked for criterion/model/evidence identity;
transport/validation failures stay unverifiable. Forwarded control-call records
and delegation summaries on stderr preserve accounting completeness separately
from verdict JSON.

Re-instruction selects every failed item and only explicitly workspace-caused
unverifiable items. Contract defects, verifier failures, transport problems,
unknown causes and exhausted budgets do not spend executor repair attempts.
Feedback is at most 300 characters, details at most three actionable items, and
is null when no actionable item remains or the attempt limit is reached.
Stopping retries never converts a failed verdict to pass.
`verifier validate-handoff` validates without rewriting and prints the supplied
handoff path on success.

## Session handoff

After pass or exhaustion, the controller generates done artifacts, remaining
criterion states, decisions with reasons, verification commands and do-not-touch
rules from transcript, contract and verdict. The hook writes to a pending name,
runs CLI handoff validation and local schema validation, then atomically publishes
`handoff.json`. On generation/validation failure it archives the previous current
handoff as `handoff.stale.UUID.json`; SessionStart reads only the current name.
Pending and stale files are retained, never injected. Exhaustion still reports
unmet work even if saving fails. A new session receives validated progress, then
requires approval for its new contract.

[Recorded demonstrations](demo.md) establish both pass-path handoff receipt and
remaining-work injection. Generation and validation failure captures deliberately
inject CLI exit 2; they establish stale-context lifecycle handling rather than
natural model/provider failure behavior.

## Deadlines and shutdown

These are source defaults; installation resolves hook timeouts as bounded JSON
integers. Child calls are capped by the remaining cumulative hook budget, with
four seconds reserved for cleanup/overhead.

| Boundary | Default seconds | Configuration |
|---|---:|---|
| SessionStart / UserPromptSubmit / Stop | 10 / 40 / 660 | `HARNESS_SESSIONSTART_TIMEOUT`, `HARNESS_USERPROMPTSUBMIT_TIMEOUT`, `HARNESS_STOP_TIMEOUT` |
| Plugin contract / verifier / handoff / validation child | 30 / 480 / 120 / 5 | `HARNESS_CONTRACT_TIMEOUT`, `HARNESS_VERIFY_TIMEOUT`, `HARNESS_HANDOFF_TIMEOUT`, `HARNESS_VALIDATE_TIMEOUT` |
| Controller CLI / HTTP generation call | 35 / 35 | `controller/config.yaml` backend `timeout_seconds` |
| Verifier total / judge / mechanical command | 450 / 120 / 120 | `HARNESS_VERIFY_BUDGET_SECONDS`, `HARNESS_JUDGE_TIMEOUT_SECONDS`, command runner default; capped by remaining verifier budget |
| Installer/demo version probe | 5 | Child runner bound |
| Demo executor | At least 2400 | Expanded for configured Stop budget and attempt count |

The plugin contract cutoff of 30 seconds intentionally precedes the controller's
35-second per-call deadline. That path cannot reach deadline-triggered controller
fallback before its caller kills it; it can still fallback on earlier transport
failure. Other caller budgets leave room for their child work and cleanup.
Plugin timeout overrides must be integer seconds in range 1–86400 (outer hooks at least
5); invalid settings fail installation/demo preflight.

Plugin child groups start in new sessions. Normal return, exceptions, deadline
expiry and SIGTERM/SIGHUP/SIGINT trigger owned-group cleanup: SIGTERM, up to two
seconds grace, SIGKILL for survivors, bounded reaping and survivor inspection.
The runner polls leader exit every 50 ms and bounds post-cleanup pipe draining
to 250 ms, preventing descendants holding pipes from delaying leader cleanup.
EPERM/ESRCH handling retries and inspects membership before per-PID signalling;
unverifiable cleanup warns on stderr. Repeated signals cannot interrupt cleanup.
The verifier owns its judge and sandbox-command groups with bounded cleanup and
reserves cleanup time within its total budget. The controller currently uses a
bounded, injectable `subprocess.run` for Codex, without a separate process-group
shutdown owner; full nested descendant cleanup is therefore not established by
the plugin runner alone. No owner can catch
SIGKILL; that case needs external supervision. Terminal-closure and complete
nested cleanup remain host checks, not consequences of offline test success.

## Hook-independent evaluation

The evaluation runner owns its contract/execute/verify/re-instruct/handoff loop.
It sets `HARNESS_NESTED=1` on executor/resume/control children so installed hooks
do not duplicate orchestration. Benchmark contract authorization comes from the
runner; it is separate from the interactive plugin approval gate.

| Configuration | Behavior and approved scope |
|---|---|
| A | GPT-6.1 Sol at medium effort, no harness; 120 frozen tasks including 20 two-session tasks. |
| B | GPT-6.1 Sol at max effort, no harness; 100 single-session tasks only. |
| C | User-filled static templates, no controller/verifier loop; 20 tasks, five per type from 20 distinct families, paired with harness on those tasks. Unfilled placeholders block execution. |
| Harness | GPT-6.1 Sol at configured medium effort in the committed full config, with generated contract, verification, up to two re-instructions and session handoff; compare handoff_success with A. |

Committed full configs use 600-second single-session and 1200-second two-session
executor deadlines; grading is separately bounded (20 seconds in full configs).
Controller/verifier budgets remain independent. The contract contains a computed
effort recommendation, but the runner launches with its configured effort; do
not infer effort switching from contract generation. These are configurations, not
completed evaluation results. No running report is used as documentation evidence.

Private graders live outside the repository and public workspaces. Only after
executor and spawned work exit does trusted grading use a fresh copy with private
graders copied in. No Codex process starts or resumes in a grading copy; later
attempts use public workspaces. Retained grading copies remain audited protected
locations, not evidence of filesystem read isolation.

The fail-closed access audit retains and hashes every execution/retry/resume JSON
stream and examines tool arguments/results for private sources/copies, aliases,
traversal, search/listing/execution and denied attempts. Missing, malformed,
truncated, unsupported or unresolved access evidence makes the audit inconclusive;
observed private access invalidates the task. Either case prevents grading and
invalidates aggregate validity. Assistant prose alone is not access. A clean
audit means no access was observed, not that access was impossible.

Reports preserve invalid-task costs, use versioned API-equivalent pricing for
executor/control/retry/fallback calls, and keep unknown accounting null. Quality
metrics use valid samples and seeded task-cluster bootstrap intervals; the final
analysis also follows the family-cluster reporting decision in
[the freeze record](eval-freeze.md). Local-minus-cheap_api parity is not measured.

## Version policy and evidence limits

[Decision 0006](decisions/0006-codex-version-policy.md) permits upgrades without
holding or rollback. Record `codex_version` per run and `cli_version` per session;
compare only same-version reports for evaluation claims. A changed version
requires a fresh hook compatibility probe plus one-task audit smoke before a
large run, and a mid-run version change stops the run.
[The registry](../plugin/VERIFIED_VERSIONS.json) includes 0.162 and 0.163;
`plugin/CODEX_VERSION` is historical, not a pin. Startup probes do not prove
production retry, handoff, persisted trust or shutdown behavior. The committed
demo captures cover the specific production paths listed in [demo.md](demo.md).
