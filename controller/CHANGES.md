# Control deadline capacity update — 2026-10-24

`HARNESS_CONTROL_TIMEOUT_SECONDS` overrides the configured per-call deadline
for codex_cli and cheap_api. Each backend reads it when constructed; unset uses
that backend's existing `timeout_seconds` (35 seconds in config.yaml). Finite
positive numbers, including fractional seconds, are accepted. Empty, malformed,
nonpositive and nonfinite overrides are input errors before any call. For
example, the evaluation runner can supply `HARNESS_CONTROL_TIMEOUT_SECONDS=120`
in the environment of its control commands without changing CLI flags or files.
This is an example capacity setting, not a measured recommendation.

Every cloud `control_call` JSON record now includes the effective
`timeout_seconds`. Each timed-out call also emits exactly one stderr line
`control_failure {"backend": "codex_cli", "model": "gpt-6-luna", "reason": "deadline", "timeout_seconds": 120.0}`
(with the actual backend/model/deadline). HTTP socket timeouts, including those
wrapped by urllib, receive the same diagnosis. This survives a later missing-key
fallback error. Missing token counts/cost remain null and contract generation
still exits 2 when accounting is unknown, including after successful HTTP
fallback. Non-timeout model/transport failures receive no deadline diagnosis.

Prompts, generation/repair logic, models, routing, call budgets, schema/output
artifacts and CLI flags are unchanged. Plugin hook budgets and persistent
controller configuration are untouched. No evaluation tasks were read. This
implements only the user's authorized capacity parameter and diagnostics under
decision 0008, with no contract-generation tuning from version 2 results.

Validation: offline controller tests cover transport deadlines, construction-time
snapshots, invalid overrides, config preservation, local exclusion, stderr
diagnostics, unchanged exit/artifact behavior, partial usage, successful fallback
with unknown accounting and non-timeout classification. Live CLI/HTTP and plugin
integration remain pending host verification. `.venv/bin/python -m pytest
tests/controller -q`: 344 passed in 14.15s.

## Assumptions

- An explicitly set invalid override is an input error (exit 1), rather than
  silently selecting the configured deadline; an unset variable uses config.
- Diagnostics are one `control_failure` prefix plus a JSON object per timed-out
  call, matching the existing `control_call` log convention. The diagnostic is
  emitted even if partial usage exists or a later fallback succeeds.
- Hook budgets remain independently enforced by the plugin. This session uses
  only mocked transports and this worktree's .venv; no network, nested Codex,
  live models or macOS sandbox-exec were attempted. Host callers choose the
  capacity value and retain it for reproducible runs.

# Judge calibration update — 2026-10-23

Judge prompt v2 checks each rubric requirement against artifact paths and lines
or symbols and records compact requirement evidence in the existing evidence
field. Pass requires support for every requirement; fail requires an inspected
contradiction; unverifiable identifies a required fact unavailable from the
snapshot. File-based behavior and test assertions do not require execution
unless the rubric explicitly demands it. Untrusted-data boundaries and the
omitted-manifest rule remain in place. The previous prompt is preserved verbatim
in prompts/judge-v1.md for comparison. Existing judgment schemas and public
controller CLI flags are unchanged.

Added 24 synthetic calibration workspaces and rubrics: 8 pass, 10 fail and
6 unverifiable. They cover partial satisfaction, misleading comments, injected
instructions, test source versus test execution, history/external facts and
omitted content. No evaluation tasks or model-generated examples were read.
Mock-backed tests exercise prompt assembly and schema parsing for every case,
both versions, approval refusal, one-call failures and confusion accounting.

The host-only command `python -m controller.measure_judge` previews a cost
estimate and requires `--i-have-approval`. Use `--prompt-version v1` for before
and `--prompt-version v2` for after, with distinct `--out` paths. Each version
permits at most 24 codex_cli generations, one per case, with no repair/retry or
HTTP fallback. Current planning estimates are USD 0.052800 per version and
USD 0.105600 for both, not caps. Reports retain hashes, configuration, per-case
judgments and accounting, accuracy, expected-status confusion matrix, errors,
latency and API-equivalent cost. Errors count as misses; unknown costs stay null.
See tests/controller/fixtures/judge-calibration/README.md for exact host commands.
Validation: `.venv/bin/python -m pytest tests/controller -q` passed all 312
tests in 14.40s. Both unapproved version previews exited 1 with the estimate
and refusal, without calls. Live calibration, nested execution and host
integration remain pending.

## Assumptions

- Synthetic fixture labels express the authored rubrics, not live calibration
  results. Mocks prove plumbing only; no semantic accuracy improvement is claimed.
- A visible contradiction determines fail even if another requirement needs
  unavailable evidence. Missing implementation in a fully inspected file can
  contradict a requirement; omitted content cannot establish absence.
- The new measurement command is controller-local tooling authorized by this
  task, not a change to the published controller judge CLI or shared interfaces.
- Before/after comparison uses the preserved v1 option on identical fixtures and
  host settings. Claude runs the approved batches on the host; no paid calls,
  nested Codex, network or macOS sandbox-exec were attempted here.

# Controller update — 2026-10-23

Contract prompt v3 addresses the first smoke measurement's contract defects.
Requested create/edit targets cannot be missing-file prerequisites. Code removes
recognized missing-target stops and adds a per-file assumption that the file may
not exist yet and may be created. Named external inputs and scope/conflict stops
remain prerequisites. Target recognition is lexical, bounded to action clauses,
and excludes inputs introduced by using/from and explicit do-not-edit clauses;
it is not a complete natural-language proof.

Every schema-valid candidate now passes static criterion validation before
return: one relative path per file/regex check, Python re compilation, supported
direct Python command forms, and detection of judge rubrics demanding execution
results. Verification commands are also checked. One repair generation names all
invalid criteria in an escaped diagnostic block. Persistent invalid criteria are
removed with one assumption each; invalid verification commands and command pairs
for removed criteria are removed too. If earlier schema retries/fallback have
already spent all three slots, this explicit degradation happens immediately.
Even removal of every criterion remains schema-valid and is disclosed for user
review. Existing accounting and production routing retain the shared three-call
budget. Schema/transport failures still follow their existing error behavior.

The controller-owned static command grammar mirrors a conservative subset of
the verifier forms without importing verifier or checking file existence.
Runtime path existence, symlink containment, installed dependencies and command
execution remain verifier responsibilities. Prompt v3 also requires all judge
rubrics to be decidable by reading workspace files alone; tests executing and
passing belong in command criteria. The lexical rubric guard catches explicit
execution demands, not every possible semantic paraphrase.

Added authored regressions for all three defects, invalid verification pairs,
regex compilation errors, escaped repair diagnostics, schema/fallback budgets,
unknown target existence and preserving external inputs. No evaluation task was
read and the original measurement request population is unchanged.


Contract prompt v2 now derives mechanical checks from request-named files,
Python modules/functions and tests. It requests py_compile for named Python
files, the named supported test command, or standard discovery with the runner
and discovery choice recorded as assumptions for review. unittest requests stay
with unittest. Missing behavior, dependencies and workspace facts remain unknown.
Scope/style requirements may still use llm_judge when objective checks cannot
express them. The template teaches only the approved py_compile, pytest,
unittest and read-only python -c command forms.

Generation now checks schema-valid contracts for mechanical success criteria
when lexical request hints identify files/modules, functions or tests. A
judge-only result gets one targeted regeneration. If the regenerated contract
is schema-valid but still judge-only, return it with one appended assumption:
"No mechanical check could be derived from the request, so every success
criterion requires judgment." Preserve its existing assumptions and criteria,
and log contract_quality_gate with action accept_degraded. Schema retries and CLI-to-HTTP fallback continue sharing the existing
three-generation budget and usage accounting. Schema-invalid output, transport
failures and exhausted budgets still fail; a first judge-only result on the
final slot still fails because no targeted regeneration can run. The gate checks criterion types;
before v3 it did not check command forms. Neither gate proves meaningful test
collection or behavioral coverage. Its lexical recognition is not a complete natural-language parser.
Schemas, public CLI flags, analyze.py metadata and escaped data blocks are unchanged.

Added authored unittest/discovery fixtures and regressions for degraded quality acceptance,
schema retries, fallback budget exhaustion, accounting and injection boundaries.
Updated existing golden responses to contain mechanical checks where required
and translate the direct script check into python -c. The original 30 measurement
request texts/IDs are unchanged; these mock responses do not measure model quality.

D-4 host measurements are recorded in LOCAL.md and STATUS. Before v2:
30/30 schema-valid, 39 criteria (4 command, 10 file_exists, 13 regex,
12 llm_judge; share 0.307692), 11 judge-only contracts and 26 without command
checks; 51 assumptions, USD 0.03600314 and 237.186616 s summed call latency.
After v2 with the old single-call adapter: 27/30 schema-valid, 38 criteria
(6 command, 11 file_exists, 12 regex, 9 llm_judge; share 0.236842), 5 judge-only
contracts and 21 without command checks; 51 assumptions, USD 0.01779202 and
295.212116 s. ambiguous-tests, scoped and data-csv failed because SingleCallBackend
refused the quality gate's targeted regeneration. These supplied host results
are not production recovery measurements; valid-output shares have different
populations. The evidence files remain untouched. Claude's revised host rerun
is pending.

Applied approved decision 0007: D-3 local Gemma 4 12B and D-5 QLoRA are
dropped. LOCAL.md and STATUS no longer describe them as pending work. The
version 1 local selector, disabled configuration and fail-closed adapter are
unchanged. Local comparison/parity is not measured.

Added `python -m controller.measure_contracts` for Claude's pending host D-4
measurement of the 30 authored requests. It prints call count and estimated
API-equivalent cost before any calls and refuses execution without
`--i-have-approval`. With the current snapshot and default planning allowances,
the estimate is USD 0.198000 for at most 90 calls. Each sample invokes the
existing contract CLI implementation using codex_cli and an internal injected
production RoutedBackend with HTTP fallback disabled in memory. Schema retries
and one targeted quality regeneration share production's three-generation
command budget; transport failures stop the sample. Production routing and public CLI flags remain unchanged.

The JSON summary records per-sample schema validity, assumptions count, counts
by check type, log-derived latency and cost, and totals including llm_judge
share, gate firings (one per affected sample), generations and USD. A code-owned
production gate log records detection even when the remaining budget prevents
regeneration. Per-sample costs and latency sum every logged generation, including
failed/rejected results. Failed samples retain their exit code and controller
errors; absent
contracts have null counts. Costs include measured failures and remain null
when accounting is incomplete. cheap_api is explicitly not measured. LOCAL.md
documents the preview, approved host command and interpretation.

Recorded Claude's completed primary gpt-6-luna contract/judge/handoff host calls
and the live plugin contract/handoff demo in STATUS. The measured latencies
15.6 s contract (20.0 s concurrent), 14.4 s judge and 13.2 s handoff informed
35 s deadlines (commit 0d57e36). These supplied results were not rerun here.
Remaining host work distinguishes HTTP fallback and production guard/retry
integration from the already completed primary CLI/demo checks.

The unknown contract cost_estimate case retains honest exit 2 under version 1;
no interface revision is planned, as directed by the user and integration
review 1. Unknown costs are never fabricated as zero.

## Verification

`.venv/bin/python -m pytest tests/controller -q`: 273 passed in 3.85s.
`git diff --check -- controller tests/controller state/STATUS-controller.md`: exit 0.
The new mocked tests exercise approval refusal, all 30 samples, log accounting,
quality/schema regeneration sequences, persistent judge-only acceptance with
exact gate logs and one appended assumption, CLI success/path output via the
measurement pipeline, final-slot rejection, transport failure after a quality
retry, three-call exhaustion, no fallback even with an API key, and
null costs when any CLI generation has unknown usage. No live call, network,
nested Codex or macOS
sandbox-exec check ran. The full suite is reserved for coordinated host
verification before merge. No staging or commit was performed.

## Assumptions

- Missing-target and runtime-rubric recognition are conservative English lexical
  checks plus prompt instructions; they do not decide arbitrary natural language.
- Static command validation intentionally does not require target files to exist.
  It accepts a conservative verifier subset and needs host runtime verification.
- When no generation slot remains, invalid criteria are removed with assumptions
  rather than attempting a fourth call. Empty criteria are allowed by the schema;
  removal is incomplete coverage requiring user review, not proof of completion.
- Claude must rerun measure_contracts and harness smoke on the host with v3.
  Network, nested Codex, live model calls and macOS sandbox-exec are unavailable
  here. The coordinated full suite remains pending before merge.

- When tests are mentioned without a runner, unittest discovery is a proposed
  dependency-free default for user review, not a verified project convention.
- The quality gate attempts to obtain at least one mechanical criterion; a
  schema-valid judge-only regeneration remains reviewable with an explicit
  assumption. Acceptance does not establish mechanical verifiability or quality.
  It does not impose a check-type quota or rewrite generated criteria itself.
- Both recorded runs are host evidence. The revised host rerun preserves the
  original 30 prompts; new unittest samples exercise offline regressions only.
- The authored requests-v1 set is the D-4 population; the original ten samples
  overlap it and are not duplicated. Only request text is sent to the model.
- The estimate uses 17,000 input and 1,000 output tokens per generation
  without cache
  discounts. These are overridable planning allowances, not hard spending caps;
  price snapshot rates are the existing API-equivalent planning rates.
- The summary is an internal controller artifact, not a shared evaluation
  report. It measures codex_cli only; cheap_api and local remain not measured.
- Host verifications and commit identity are supplied by the user. The plugin
  evidence path is recorded without independently reading or rerunning it.
- No PR exists. This file supplies the reviewable change summary and Assumptions.
