# Shared interfaces, version 2

Status: version 2 approved by the user on 2026-10-23 in
[0009 task-level false done](decisions/0009-task-level-false-done.md).
schemas/VERSION is 2. Version 1 was approved on 2026-10-21. Decisions
[0002 judgment](decisions/0002-judgment-schema-proposal.md),
[0003 evaluation report](decisions/0003-evaluation-report-schema-proposal.md) and
[0004 backend/guard](decisions/0004-codex-cli-backend-and-nested-guard-proposal.md)
are the original approved change records. Version 1 was published ahead of the planned
2026-10-24 freeze; later revisions require approval, a record and a version
increment. Published contracts do not establish implemented or measured runtime
behavior. Each owning role's STATUS records implementation evidence.

Version 2 adds only the required `metrics.task_false_done_rate` entry and the
`claimed_complete_task` sample unit. Reports with that entry are version 2;
version 1 reports omit it and validate against the original schema preserved in
decision 0003. No report version field is added. Previously produced full-a,
full-b, smoke reports and pilots remain valid version 1 documents; compare them
only through tools that accept both versions. Report-interface version and
task-set version are separate identities. Publication does not migrate reports.

## Setup and checks

Use Python 3.11 or newer. From the repository root:

```sh
make skeleton
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
make validate-schemas PYTHON=.venv/bin/python
make test PYTHON=.venv/bin/python
```

make skeleton recreates empty role directories without adding implementation
files. Setuptools includes controller, verifier, eval, plugin and the preserved
legacy harness. Default pytest collection covers tests/lead, tests/plugin,
tests/controller, tests/verifier and tests/eval. For a package check use
TEST_PATH=tests/ROLE. Legacy top-level experiments/tests retain their separate
setup; a role-suite pass does not establish their Docker/Chromium integration.

## Six CLI contracts

Successful stdout contains exactly one path plus a newline. Logs go to stderr;
errors do not print a success path. Exit 0 means successful computation, 1 input
error and 2 internal error. Fail/unverifiable judgments, failed verification and
recorded invalid evaluation tasks are computation results, not input errors.
Validate inputs before invoking models. All JSON outputs validate locally.

| CLI | Arguments | Output / successful stdout | Exit codes |
| --- | --- | --- | --- |
| `python -m controller contract` | `--prompt FILE --handoff FILE_OR_none --cases DIR --backend codex_cli_OR_cheap_api_OR_local --out contract.json` | contract.schema.json; stdout is --out path | 0 / 1 / 2 |
| `python -m controller handoff` | `--transcript PATH --contract contract.json --verdict verdict.json --backend codex_cli_OR_cheap_api_OR_local --out handoff.json` | handoff.schema.json; stdout is --out path | 0 / 1 / 2 |
| `python -m controller judge` | `--criterion JSON_FILE --artifact PATH --backend codex_cli_OR_cheap_api_OR_local --out judgment.json` | Input: judgment-input.schema.json; output: judgment.schema.json; stdout is --out path | 0 / 1 / 2 |
| `python -m verifier check` | `--contract contract.json --workspace DIR --transcript PATH --attempt N --out verdict.json` | verdict.schema.json; stdout is --out path | 0 / 1 / 2 |
| `python -m verifier validate-handoff` | `--handoff handoff.json` | Validate existing handoff without rewriting; stdout is supplied handoff path | 0 / 1 / 2 |
| `python -m eval run` | `--config YAML --out eval/reports/NAME/` | --out/report.json validates with evaluation-report.schema.json; stdout is supplied directory path | 0 / 1 / 2 |

FILE_OR_none means a file path or literal none. Backend is required and accepts
exactly codex_cli, cheap_api, local. No other command/flag changes are introduced.
Judge accepts a full criterion object with id, description and check, without
an array or contract wrapper; only llm_judge checks execute it. Missing
comparison evidence can yield unverifiable; unreadable CLI input paths are
input errors. criterion_id must equal the input id and evidence includes
llm_judge; code enforces these cross-field rules.

## Control backend and nested guard

Primary workflow/config explicitly selects codex_cli with gpt-6-luna through
the existing logged-in CLI. cheap_api uses the same gpt-6-luna over HTTP
Responses API with its configured environment API key. Local Gemma 4 12B is
stage two, never an implicit fallback. Configuration supplies models, endpoints,
executables, deadlines and fallback policy. Reuse login without reading/copying
auth.json or deriving HTTP credentials from it; do not modify persistent login,
config or trust.

A codex_cli transport failure/unavailability/deadline may transition once to
cheap_api if its key and budget exist. Ordinary fail/unverifiable judgments do
not trigger fallback. At most three generation calls are allowed per command
across initial generation, retries, fallback and schema regeneration. Fallback
uses one slot; remaining retries stay HTTP. Missing credentials/budget yields
exit 2. Explicit cheap_api bypasses CLI. Unavailable local is an explicit error.
Keep actual model/backend, usage, pricing and fallback reason for every call.

Inject subprocess execution with shell=False, piped input and bounded deadlines.
Consume --json events as logs/accounting and --output-last-message as final JSON.
Use the supported --output-schema strict adapter, then validate locally and
overwrite code-owned identity/effort/usage. CLI events never become the
controller command's successful stdout.

Every LocalHarnessMaker hook must first compare HARNESS_NESTED to the exact
string "1". HARNESS_NESTED=1 means exit 0 immediately with zero bytes on stdout
AND stderr, before reading stdin, loading state/config, importing
controller/verifier, creating files, logging timing, spawning processes or
handling the normal path. This precedes whole-script exception/stub handling.
Empty output is neither {} nor a newline. Unset, empty, "0", "true" and "01"
preserve normal behavior. Normal failure/timing requirements apply unguarded.

Set the guard in a copied environment for every controller-owned Codex child,
retry/resume/repair and wrapper capable of launching Codex. Role 5 also sets it
for runner-owned executor/resume children so its independent loop does not
execute twice through hooks. Never mutate parent environment/persistent config.
Direct-user sessions normally leave it unset. Other plugins' hooks require
separate verification. Version 1 specifies the guard; startup probes do not
prove its implementation.

## Six schemas and eight examples

All schemas use JSON Schema draft 2020-12 and closed objects. Original contract,
verdict and handoff field shapes are unchanged. Four check types remain
exclusive: command, file_exists, regex, llm_judge. Command expected has required
exit_code and optional exact stdout including newlines; omitting stdout checks
only exit status while retaining evidence.

| Schema | Example | Purpose |
| --- | --- | --- |
| contract.schema.json | contract.json | Original FastAPI endpoint/test contract; code computes effort/cost metadata |
| contract.schema.json#/$defs/referencePrompt | prompt.json | JSON string request fixture; not a new CLI envelope |
| verdict.schema.json | verdict_pass.json, verdict_fail.json | Passing second attempt and failing/unverifiable first attempt |
| handoff.schema.json | handoff.json | Resume the failing first attempt |
| judgment-input.schema.json | criterion.json | Exactly one full llm_judge contract criterion; locally references the existing definition |
| judgment.schema.json | judgment.json | criterion_id, status, reason, evidence, model and usage |
| evaluation-report.schema.json | evaluation_report.json | Run metadata, audited task results, seven metrics, accounting and aggregate validity |

Schema filenames are under schemas/ and example filenames under
schemas/examples/. make validate-schemas validates all six schema definitions
and all eight samples, with local-only reference registration and date/time
format checks. Missing required files, unmapped examples, broken references or
invalid samples fail the target. It executes no embedded verification command
or network/model call. CI already runs this target and pytest.

Empty/all-judge contracts remain representable for verifier quality warnings;
unverifiable never passes. Verdict attempts start at 1; passing verdicts have
all passing items and null re-instruction. Failed verdicts may use null at the
retry cap; non-null re-instruction is at most 300 characters. Code enforces
unique/corresponding criterion IDs, retry caps and evidence provenance.

All examples are synthetic specifications, not live task/model results. The
original FastAPI contract retains zero placeholder tokens/cost; the new report
and judgment use clearly labeled fixture rates, paths and hashes. Zero in a
fixture is not permission to replace unknown production usage with zero.

## Evaluation, accounting and confidence intervals

Use the approved access audit from decision 0003. Private graders are outside
the repository and every public executor workspace. After executor and spawned
work exit, create a fresh trusted grading copy and copy in graders; copied_at
must be strictly after exited_at. Never execute/resume Codex in grading copies,
expose those copies to future executor turns, or return private test content to
controller/executor. Each later attempt uses public inputs and a fresh
post-exit grading copy. The old deny-read prerequisite from decision 0001 is
superseded; clean audit is not proof of isolation.

Retain every execution/retry/resume --json stream and SHA-256. Inspect tool
arguments/results for canonical grader/copy paths, children, aliases/traversal,
read/list/search/execute/write and denied attempts. Record log/line/tool/path/
operation/evidence. Matches are access_detected; missing/malformed/truncated/
unsupported streams and unresolved operands are inconclusive. Either makes the
task invalid with reasons and no grading result. Assistant prose alone is not
access. Any invalid task makes report validity=invalid; clean-subset metrics
are diagnostic only. Audit-clean failures, errors and timeouts remain valid
quality samples. Record observed model/effort and invalidate mismatches.

Reports preserve metadata/config/task-set hashes, price/bootstrap provenance,
per-task attempts/segments/log hashes, audit, trusted grading timestamps,
evidence-backed handoff outcomes, claim counts, calls and costs. Runtime checks
enforce identity/count/cost/ordering invariants beyond JSON Schema. Two-session
handoff records day2_pass and user_restated_day1_context with evidence;
missing observation invalidates rather than silently dropping a task.

| Metric | Definition | sample_size unit |
| --- | --- | --- |
| pass_rate | Passing valid tasks / valid tasks | valid_task |
| false_done_rate | claimed_without_evidence / claimed items from valid tasks | claimed_criterion |
| task_false_done_rate | Claimed-complete valid tasks failing hidden grading / claimed-complete valid tasks | claimed_complete_task |
| cost_per_pass | All attempted tasks' executor + control API-equivalent USD / passing valid tasks | attempted_task |
| avg_attempts | Mean executor attempts per valid task | valid_task |
| handoff_success | Eligible valid two-session tasks passing without restated context / eligible valid two-session tasks | eligible_two_session_task |
| parity | Local pass_rate minus cheap_api pass_rate on matched valid tasks | matched_task |

For `task_false_done_rate`, both numerator and denominator exclude invalid
tasks, which remain visible through existing `invalid_reasons` and `validity`
fields. Apply the claim extractor rules from `verifier/claims.py` to the retained
final message of the last session, identically for A, B, C and every harness
configuration. Earlier messages, tool output and controller/verifier messages
cannot substitute. A task with no retained final message is undefined and
excluded from both populations with a reason; do not infer an absent claim.
`sample_size` counts claimed-complete valid tasks with retained final evidence.
Retain source segment/hash, claim evidence and exclusion reasons in existing
artifact references; add no per-task fields. Role 5 owns implementation in
`eval/metrics.py` and the report builder. Existing criterion-level
`false_done_rate` stays unchanged. Use retained evidence only, with no new
executor/judge calls or grading of invalid tasks. The synthetic report example
has no retained final message, so its new metric is null with an explicit reason.

Each metric has value, sample_size, sample_unit, ci95 and undefined_reason.
ci95 specifies level=0.95, lower, upper and
method=task_cluster_percentile_bootstrap. Use seeded task clusters, default
10000/minimum 1000 resamples and 2.5th/97.5th endpoints, with paired tasks for
parity. Preserve claims/sessions/attempts within clusters. Include invalid
cost clusters for cost_per_pass. Zero original/bootstrap denominators or
missing required accounting yield null value/bounds and an explanation.
Runtime code checks CI order/bounds; small-sample CIs may be degenerate.
Parity keeps the existing local-minus-cheap_api definition, with identical
hash-pinned task set, seed, executor model/effort and Codex version; it is
undefined without that pair, including a standalone codex_cli report.

All money fields are API-equivalent USD, from pinned per-model input/cached/
output rates. Include executor, contract, handoff, judge, failed/invalid calls,
regenerations and fallbacks once. Cache tokens are a subset of input tokens;
do not bill reasoning output twice. Unknown usage/rates make affected costs
and aggregates null, not zero. Logged-in CLI is not free; local Gemma requires
an explicitly sourced equivalent API price or null. Judgment model/usage are
code-owned; private per-call logs retain actual backend/model/pricing when
several calls contribute to one output.

## Installed hook evidence and remaining integration

The published [hook contract](hooks-contract.md) is the installed-version source
of truth under AGENTS.md section 3.3. Pin: codex-cli 0.162.0-alpha.17.2. Captured
interactive/exec startup runs establish all three hooks, additionalContext
visibility and one bounded Stop continuation. Stop did not resubmit
UserPromptSubmit. Preserve contract state across continuation. Normal Stop
uses decision=block/reason for unmet work; pass/retry exhaustion allows ending.
SessionStart/UserPromptSubmit use hookSpecificOutput.additionalContext with
the corresponding hookEventName. transcript_path can be null. SessionEnd is
observe-only and unused. The transcript wire format is not stable.

Production handoff-save point, null transcript handling, other SessionStart
sources, persisted trust, approval/retry limits and the nested guard require
owning-role integration tests. Runtime limitations are implementation work, not
unapproved schema gaps. Do not change version 1 silently to accommodate them.

## Assumptions

- FILE1/FILE2/FILE3 in the approval refer to the three immediately preceding proposals 0002, 0003 and 0004, approved on 2026-10-21.
- Explicit permission covers updating prompts/03-controller-engineer.md and prompts/05-eval-engineer.md; other roles' implementation files and STATUS remain untouched by Role 1.
- Version 1 publishes approved shared contracts; runtime backend/hook/runner completion requires separate evidence from the owning roles.
- Synthetic fixture prices and unknown-accounting/null policies are preserved exactly as approved; no live model/account/price result is inferred.
