# Evaluation runner

The runner writes `report.json` against the approved
`schemas/evaluation-report.schema.json`, with offline schema/format validation
and runtime checks for IDs, counts, ordering, costs and event hashes.
`eval/report.schema.json` is retired and retained only as a reference to that
shared schema. Historical reports in `reports/baseline-a-first-task/` remain
unaltered provisional evidence; they have not been reclassified as approved
reports or rerun.

The frozen command is `python -m eval run --config FILE --out DIR`.
Successful stdout is exactly the supplied output directory plus a newline;
exit codes are 0 for computed reports (including invalid tasks), 1 for input
errors and 2 for internal errors. Configs use the JSON subset of YAML.
Completed version-1 checkpoints do not call models again. Historical provisional
checkpoints require an explicit offline migration or a fresh output directory;
they are not silently relabeled as version 1. Interrupted or unsupported
streams remain invalid even after a later successful continuation.

Private graders must already exist outside the repository, supplied through
`LHM_PRIVATE_GRADERS` in the trusted parent environment. This session does not
create them. Each task's external directory contains `test_*.py`; optional
`audit-names.json` lists historical filenames. Only after all executor work
exits and the access/settings audit passes does the runner copy graders into
a fresh trusted grading copy under the separate temporary
`lhm-retained-grading/` location. Copies are retained for review, outside
executor runtimes. Every task audits that retained location, every other
`lhm-eval-*` runtime in the temporary directory (including previous runs),
legacy grading copies in its own runtime, and the private source root.
A later executor can reach these paths because reads are not denied;
observed access invalidates the task. External raw logs are retained;
public evidence uses redacted labels and hashes.
Native logs are referenced with hashes as well as executor JSON streams.
Each task also writes `access-audit.json`, containing every error and match with
log name, line number and evidence hashes. The audit scans the entire file after
an error, so multiple unsupported records appear in one run. The same complete
audit remains in `result.json`; the shared report references the audit artifact.

Every executor, resume and control child uses a copied environment containing
`HARNESS_NESTED=1`. Executor environments exclude private locations and API keys.
The runner uses a temporary Codex home and the existing external auth symlink;
it never copies credentials or changes global configuration.

The access audit checks tool command, file-change, function-call and tool-result
events for private grader sources/copies, `~/.codex`, the sibling `codex-bridge`
folder and this repository outside the task workspace. URL/JSON encodings,
relative traversal, existing symlink aliases, denied attempts and retries are
covered. Assistant prose is excluded. Missing, truncated, unknown, unpaired or
unfinished tool evidence and unresolved operands make the audit inconclusive.
Shell commands use shlex, event cwd/workdir and tracked cd/pushd/popd locations.
Literal zsh/bash/sh `-c`/`-lc` wrappers are unwrapped before operand analysis;
single or double wrapper quotes do not count as quotes inside an operand.
Quote checks use each inner word's own spelling. Unresolved quoting/escaping
inside a path remains inconclusive.
A glob is bounded when its static directory prefix resolves inside the workspace
and no `..` component follows its first wildcard. Such globs may audit clean
even with no current matches. Concrete matches still resolve through symlinks
and are checked for protected access; globs outside that boundary remain
inconclusive unless protected access is detected. Values of rg `-g`/`--glob`,
find `-name`/`-iname`/`-path`, and grep `--include` are filter patterns rather
than filesystem operands. Recursive commands still audit their start paths,
including the current directory when implicit.
Parse failures, named-user tildes and other unresolved expansions remain
inconclusive; concrete canonical paths compare without case. Environment
variable expansion, including `$HOME`, remains conservative.
Recursive search/list/copy/archive operands covering an ancestor of a protected
root are access_detected. Fingerprints cover distinctive hidden grader lines
of at least 16 normalized characters from `ROOT/<task>/test_*.py`, where task
directories have non-dot names. Root-level files, deeper descendants,
dot-directories (including quarantine/reference copies) and symlinks never feed
fingerprints. The entire private root remains protected against path access.
Source contents are deduplicated by SHA-256 before parsing. The runner and
read-only re-audit share one fingerprint/public-corpus analysis across tasks,
retries and streams per invocation; a new invocation gets a new cache.
A candidate
must contain a number or string literal absent from every public task's
`prompt.md`, `day2.md`, `expected.json`, `meta.json` and `workspace/` files;
lines already present publicly, docstrings, module entry guards and unittest
launchers are excluded. Literal comparison includes decoded strings and numeric
spellings, with conservative substring exclusion for common values.
Only command `aggregated_output` and function/custom tool output contents are
matched. Executor-authored patches, file changes, arguments and metadata are
never fingerprint evidence. File changes and patches are checked only through
their target and move paths; authored content/diffs are not operands or path
access evidence, even when they contain `$`, backticks, quotes or path strings.
Distinctive hidden output remains access_detected even when a read hides its path.
Only hashes, labels and redacted evidence are retained in audit results.
Decode-and-execute pipelines such as `base64 -d | sh` are inconclusive.
For pinned codex-cli `0.162.0-alpha.17.2`, native records include `session_meta`,
`turn_context`, `response_item`, `event_msg`, `world_state` and
`token_usage_record`. Snapshot records require boolean `full` and object `state`;
usage records require a usage object with nonnegative integer input/output
counts, and validate supplied turn/thread counts. The entire snapshot/usage
record, including nested keys and values, is scanned for private paths, aliases,
canonical traversal/symlink targets. A match reports
that a private location reached executor context and prevents grading. These
records are metadata; ordinary session settings are not shell operands.
For `0.163.0-alpha.11.1`, `event_msg.thread_settings_applied` is also metadata.
Its required thread identity and settings fields are shape-checked, including
model/provider, approval settings, managed filesystem/network profile, cwd,
workspace roots, effort, collaboration settings and disabled plugins. The full
record, including extra keys/values, receives the same private-marker scanning
as `world_state`; malformed shapes and other unknown kinds remain inconclusive.
Applied model/effort evidence includes both this event and `turn_context`;
conflicts leave settings unverified. Both sources appear in session-evidence.jsonl.
The synthetic 34-record `native-session-0.163.jsonl` fixture preserves the host
smoke's record order and line-9 settings structure without absolute user paths.
Native `event_msg.item_completed` command/file-change records are inspected,
while user/assistant message items remain prose. Native `custom_tool_call.input`
and `custom_tool_call_output` are paired; decoded input operands and output paths
are inspected, and fingerprints apply only to outputs.
Literal `exec` JavaScript wrappers around `tools.exec_command` and
`tools.apply_patch` are decoded without executing code. Every literal shell
command and its literal `workdir` (when supplied) is audited separately;
JavaScript glue and patch contents are never parsed as shell commands. Patch
targets receive path checks, including moves and bare symlink filenames.
Dynamic commands (including string concatenation), dynamic directories, unknown
tools and unsupported custom code stay inconclusive. Other unknown record/item kinds
also stay inconclusive. The synthetic 33-record regression fixture preserves
the supplied host session's structure and record order, with categorical
discriminators retained and all task, identity, path and usage content replaced.
Additional synthetic cases preserve the retained interval-union session's
line-23 patch-plus-unittest call and line-25 absolute-path FileChange map.
Detected or inconclusive access invalidates the task and aggregate report and
prevents grading. This is observed access auditing, not filesystem isolation
or proof that all unlogged activity is safe. Dynamic execution and additional
installed-version event forms require host review before measurement.

Offline re-audit of a finished run (no executor/controller/judge calls):

```sh
.venv/bin/python -m eval.runner.reaudit --private-root "$LHM_PRIVATE_GRADERS" --out eval/reports/pilot-a/
```

Here `--out` identifies the existing run directory to read. The command loads its
checkpoint and report, requires finished tasks, and audits the original external
`exec-*.jsonl` streams plus all native session logs under each retained runtime.
It uses each task's own `PrivateGraders`, workspace, repository and the runner's
`audit_roots(runtime)` grading/cross-runtime roots. Retained log hashes/counts and
grader hashes must match the original audit; unavailable, lost or changed evidence
is inconclusive unless access is detected. It prints one JSON row per task with
only `task_id`, `status`, `error_kinds` and `match_labels`; no paths or contents.
It writes nothing and does not replace the report, checkpoint or stored audits.
Exit 0 means re-audit computation completed, including detected/inconclusive rows;
exit 1 means the finished-run inputs or command arguments were unusable. Review
the rows on the host before choosing a fresh pilot A rerun directory. A clean
re-audit is observed cleanliness, not a new quality result or proof of isolation.

Harness configs select `harness=true`, an explicit `control_backend` and a
`reinstruction_limit`. The runner calls `python -m controller contract` with
an empty public case library and no handoff for day 1, validates the contract,
injects its JSON into the day-1 executor prompt, then calls `python -m verifier check` with
native transcript evidence and the public workspace. Only its bounded non-null
re-instruction resumes the same executor session. It supplies
`HARNESS_BACKEND` and `HARNESS_MAX_ATTEMPTS` in the verifier's copied environment.
Private grading is outside this loop. Contract/verdict artifacts and control
stdout/stderr are retained. `configs/harness-mocked.yaml` is a host-verification
candidate, not a measured run. Unit tests mock every controller/verifier/model
subprocess; synthetic grading remains a local process.

Reports compute seeded task-cluster bootstrap metrics (10000 resamples;
minimum 1000). Invalid tasks leave quality samples but retain costs. Any zero
original/bootstrap denominator or missing accounting produces null values and
bounds. Output tokens already include reasoning; cached input is an input
subset. `prices.yaml` pins `openai-standard-short-2026-10-22-v1`, using the
user-supplied Claude host fetch of OpenAI pricing (checked 2026-10-22): Standard
tier, up to 272K input tokens. The source records the URL and absence of a
provider version/date. Unknown models/tiers, long-context turns and incomplete
tokens retain null costs; null propagates to accounting and cost_per_pass.
Standard is the CLI baseline assumption when no tier evidence is present;
observed non-Standard tiers override it. Subscription usage is not zero-dollar
API usage. Historical reports are preserved. Control CLI artifacts do not expose a complete
per-call accounting ledger; actual fallback transport/model and costs remain
unobserved. `control_model` and control costs stay null. Full done-claim
extraction and hash-pinned paired parity are pending; false_done_rate and parity
are undefined with reasons rather than incomplete headline measurements.

Task set version 1 contains 100 single-session and 20 two-session public tasks
across four types, all marked `frozen=true`. The user authorized freezing after
Claude's host verification and independent mutation testing (commits `80205d3`
and `ad7d7be`); no surviving mutant changes specified behavior.
`GRADERS-PENDING.md` retains the validation inventory despite its historical name.
Only the freeze flag changed in public task files; historical review fields remain
unchanged. Further task-content changes require a separate version 2.
The runner rejects any selected task whose freeze flag is missing or not boolean
true before external work, including when resuming a checkpoint.
The published freeze record in `docs/eval-freeze.md` pins commit `7cdaf3b` and
digest `b78913b04280f6696d419d2afdc96b152675973d82f05199ddef848986285d1f`.

The combined r5-full-001/r5-full-002 implementation runs two-session tasks.
Two-session tasks run day 1 with `prompt.md` in a fresh public workspace, then
start a new executor session in that same workspace after day 1 exits. Day 2
receives exactly the UTF-8 bytes of `day2.md` as stdin. Baselines add no context;
executor-authored files such as `HANDOFF.md` are the only carry-over. Day 2
never resumes day 1. Transport retries and verifier reinstructions may resume
their own day's session.

In harness mode the runner generates `handoff.json` after day 1 with the frozen
controller handoff CLI, using the day-1 native transcript, contract and last
verdict. It calls `verifier validate-handoff` without an `--out` flag, then
passes the validated file to the day-2 controller contract. The day-2 contract
is supplied separately through Codex's `developer_instructions` configuration;
the user prompt remains exactly `day2.md`. All children receive
`HARNESS_NESTED=1` in copied environments. Hooks do not own this loop.

Control outputs are pinned in a runner-owned hash manifest. Evidence publishing
never searches executor workspaces or follows symlinks. An output already
present before its trusted producer runs invalidates the task with
`runner_control_file_preexisting`; changed pinned inputs remain control errors.
Handoffs choose only pinned `verdict-N.json` files with numeric N. Unowned files,
including `verdict-99.json` and `verdict-final.json`, cannot become handoff input.

Hard-crash recovery resumes the active session and preserves completed days.
Audit-clean day-1 timeouts/errors can continue to day 2. Regrade preserves final
executor timeout/error outcomes and invalid pre-day-2 tasks while grading other
eligible tasks in fresh trusted copies.

Both days' event and native logs are retained and audited. A missing native
settings observation for either process invalidates the task. Private grading
runs once, in a fresh trusted copy after day 2 exits. Checkpoints retain each
segment's workspace exit hash and the final workspace hash. Regrade checks
both days' recorded hashes, distinct session identities, retained prompt bytes
and public prompt digest before grading the unchanged final workspace. Day-1
hashes are historical runner observations; the changed final workspace cannot
reconstruct a day-1 state. Regrading adds no executor attempts or usage.

`handoff-evidence.json` records the delivered day-2 prompt SHA-256, public
`day2.md` SHA-256, retained delivered prompt path and initial day-2 attempt.
Missing, changed or unverifiable observations invalidate the task.
`handoff.day2_pass` reflects final trusted grading, and
`user_restated_day1_context=false` is backed by the exact prompt comparison.
`handoff_success` uses valid observed two-session tasks, including grading
failures, as its denominator; an empty denominator yields null. Both days'
attempts and executor costs are summed once within the task cluster.

`configs/full-a.yaml` (medium) and `configs/full-b.yaml` (max) contain all 120
frozen tasks in the same lexicographic order and seed. Both preserve pilot
limits, with the optional runner-owned `task_timeout_seconds` map overriding
individual process deadlines (1200 seconds for two-session tasks, 600 for
others). `grading_timeout_seconds` remains 20. These configuration fields do
not change the frozen CLI flags or report schema.

[Decision 0006](../docs/decisions/0006-codex-version-policy.md) requires matching
version evidence: `full-a`, `full-b` and `smoke-two-session-a` select
`codex-cli 0.163.0-alpha.11.1`. Historical pilots used `0.162.0-alpha.17.2` and
supply diagnostic planning data only for these newer runs. The runner checks
the installed version before each executor launch and halts if it changes.
Missing/mismatched native per-session `cli_version` instead invalidates only
that task (`missing_cli_version_evidence` / `mismatched_cli_version_evidence`),
preserving its costs and the complete report. Compare only identical versions:
`python -m eval.runner.compare_versions REPORT_A REPORT_B` refuses mixed versions.
Every new version needs a hook compatibility probe and one-task audit smoke
before large runs. The supplied 0.163 host hook probe passed. The first host
two-session smoke stopped correctly before day 2: its audit was inconclusive
only for the new line-9 settings event. That record is supported offline now;
Claude must rerun the smoke in a fresh output directory. Audit smoke and
production behavior remain host checks.

STOP-3 estimates include both executor days and up to three generations per
controller/judge command across retries and fallback. A no-retry two-session
harness task already bounds 11 calls before judge criteria; it requires the
existing estimate/approval process. Per-task timeout overrides must still select
configured tasks and lie in (0, 3600].

Full runs remain **on hold**. The STOP-3 estimate is in
[reports/full-estimate.md](reports/full-estimate.md): 140 sessions per
configuration, about $4.10/$6.03 API-equivalent USD from pilot session averages,
and approximately 56/84 plan percentage points using the user-supplied pilot
deltas. These are planning proxies, not spending caps or quota guarantees.
Claude must host-verify the smoke, review pilots and ask the user again before
full execution. Exact bundled full/pilot configurations with published
estimates pass configuration validation; that is not user approval.

Claude's host smoke (one two-session task, harness off, medium; no run here):

```sh
.venv/bin/python -m eval run --config eval/configs/smoke-two-session-a.yaml --out eval/reports/smoke-two-session-a/
```

The smoke requires the existing host login and separately supplied private
grader environment. It must confirm native evidence, two distinct sessions,
exact day-2 prompt delivery, exit hashes and one post-day-2 grade. Harness
`developer_instructions` delivery and boundary recovery still need host
verification; mocked tests establish orchestration only.

Offline verification:

```sh
.venv/bin/python -m pytest tests/eval -q
git diff --check -- eval tests/eval state/STATUS-eval.md
```

No executor model, nested Codex, network or macOS sandbox-exec is invoked in this
session. Live CLI compatibility, production retry/guard behavior and sandbox
operation are pending host verification. Freeze preparation is complete; the
final host digest and Role 1 record remain pending. No pilot, full run or
quality/cost comparison is claimed.

## Assumptions

- The user's priority order supersedes the older STATUS claim that the shared
  report interface is provisional; version 1 is approved.
- The user's report of Claude's host verification authorizes the version-1
  metadata freeze; private validation is not rerun in this sandbox.
- A reference-only compatibility schema retires the provisional definition
  without deleting a file or changing the shared interface.
- Model accounting absent from the frozen CLI output remains unknown; the
  runner does not infer actual fallback transport or model identity.

Incomplete runs halt without publishing a report and retain checkpoints for
recovery. A report requires the complete configured task set; this preserves the
shared schema without treating partial STOP-E1 evidence as a valid comparison.

Account usage limits are resumable STOP-E1 infrastructure stops. The runner
recognizes usage-limit wording only in `--json` `error.message` and
`turn.failed.error.message` (or direct `message`) events. Control-call evidence
comes from retained stdout/stderr, including nested `control_cli_events` logs.
Assistant/tool prose and ordinary errors do not trigger this classification.
It halts before any runner retry, day 2, grading or next task, prints the original
limit message and reset time to stderr, exits 2 and prints no success path.
The interrupted task has no result.json or checkpoint outcome; no report.json
is published. Rerun with the same config and `--out` after the limit resets:
existing sessions resume, or start fresh if no thread was created; pending
control operations retry without rerunning completed executor work. Failed
control streams and partial outputs remain hash-pinned under
`control-interruptions/`, with redacted report copies. All retained executor
attempts still count; missing usage/cost stays null. Control commands finish
within their existing bounded subprocess deadline; the runner checks their
retained events on return and makes no later call on a limit.

Offline grader mutation validation uses
`.venv/bin/python -m eval.runner.validate_graders --private-root "$PRIVATE_ROOT" --tasks all --mutants 10000`.
The limit applies per task, across application and submitted regression overlays;
10000 currently covers every generated mutant. Operators replace comparisons,
swap binary addition/subtraction and boolean and/or, increment integer literals,
replace returns with None, drop slice bounds/steps, and remove not. Each mutant
has exactly one AST edit. Ordering is deterministic (manifest file order, then
AST traversal and operator order), with duplicate source results removed.

Mutation mode prints only task identifiers and killed/survived/equivalent counts.
It returns success only when each task kills at least 90% of its non-equivalent
mutants. A passing reference control is required under the same two-second
per-grading deadline; assertion failures and deadline expiry kill mutants.
At most four offline task validations run concurrently. No executor is launched.

Review data is written beneath the explicitly supplied private root, in
`.mutation-records/TASK.review.json`. Manually reviewed equivalences belong in
`.mutation-records/TASK.equivalences.json`, as an object mapping review IDs to
objects with a nonempty `reason`. IDs bind the entire reference overlay, mutated
source, target and public prompt/expected hashes. Survivors are never classified
equivalent automatically. Validation and mutation workspaces, logs and grading
copies stay under the private root and are cleaned on exit, including failures;
evaluation runs retain their existing grading-copy behavior.


## Ten-task A/B pilot preparation (2026-10-22)

`configs/pilot-a.yaml` and `configs/pilot-b.yaml` pin identical task lists, seed 0,
CLI version, zero retries, harness off and 600-second task deadlines. A uses
medium; B uses max. The [estimate](reports/pilot-estimate.md) documents deterministic
family selection, the 3/3/2/2 type split, token/cost calculations, assumptions
and host commands. The legacy single-task `configs/pilot.yaml` stays unchanged.
The exact bundled pilot configs with the published estimate pass the batch
preflight and print the estimate to stderr; other batches of ten or more calls
remain blocked. Host approval is still required before the pilot is run.

`run-diagnostics.json.executor_runs` and task `result.json.executor_runs` retain
per-attempt tokens and primary plan used_percent from native token_count events,
with timestamps and complete rate_limits. Before is the last native observation
at or before process start; after is the last during the process. Missing
observations stay null; first_observed_during_run is separate. This does not
claim a true pre/post measurement when the native log has no such sample.
Plan usage cannot be predicted from tokens. Existing raw/native evidence and
hash retention remain in place; no frozen report fields were added.

Task set v1 is frozen at `7cdaf3b`, full-set digest
`b78913b04280f6696d419d2afdc96b152675973d82f05199ddef848986285d1f`,
recorded in `docs/eval-freeze.md`. This supersedes the earlier pending-freeze
notes below/in historical changes. Pilot metadata currently fingerprints the
selected subset using the existing runner algorithm; compare identical A/B
subset hashes and retain the full source-population digest in the estimate.
SC-5 results, five manual A reviews, host prerequisites and full-run approval
remain pending. No executor/model or private-root access occurred in preparation.

## Pilot-B audit shapes and retained-workspace regrading

Code-mode audit extracts each direct `tools.exec_command(...)` and
`tools.apply_patch(...)` call independently of arrays, Promise combinators,
loops, spread in display output and other surrounding JavaScript. Only literal
`cmd` and optional `workdir` operands establish resolved execution. Tool aliases,
computed/optional tool access, unknown tools, eval/Function and unresolved
callables remain inconclusive. Command-object spreads remain unresolved because
they can override an operand. Shell rules apply to extracted commands, never to
JavaScript glue or authored patch contents. Nested `-lc` wrappers are decoded
with shlex; the pilot's adjacent quote segments resolve to the literal `!.git`
and `!.aws` patterns. Exec `file_change.changes` lists of `{path, kind}` use the
same target/move checks as native FileChange dictionaries. Both sides of path
comparisons, and private-path redaction, recognize `/var` and `/private/var`.

The runner now saves its configuration and a `workspace_exit_sha256` in the
checkpoint immediately after each executor process exits, before audit,
verification or grading. Each segment also retains that hash. The deterministic
manifest includes every relative path, entry type, file SHA-256, permission mode
and symlink target; caches are included, and symlinks are never followed.
Hashes are not backfilled for historical executions.

On the host, regrade a complete run without new executor/controller/judge calls:

```sh
.venv/bin/python -m eval.runner.regrade --private-root "$LHM_PRIVATE_GRADERS" --from eval/reports/SOURCE --out eval/reports/NEW
```

`NEW` must be fresh and separate from the source, retained runtimes and private
storage. Every configured task must have a runner-recorded exit hash, and every
retained workspace must match before any output or grading copy is created.
Missing hashes or changed workspaces cause a clear refusal. Regrade also checks
the source report, selected public/private task inputs and retained log/grader
manifests. It re-audits all tasks, grades every audit-clean workspace through the
same `grade()` function in a fresh post-exit copy, and preserves executor/control
calls, costs and observations. Other invalid reasons remain invalid. It writes
new results, audits and a complete schema-validated report, recalculating quality
metrics over the whole run. It never resumes Codex or writes to the source run
or original runtime. Grading process output uses a separate retained runtime.

`NEW/run-diagnostics.json` records the source directory, source report SHA-256,
audit implementation file hashes and all workspace-hash checks. No shared report
schema fields were added. Successful stdout is `NEW` plus a newline; input
refusals exit 1, internal errors exit 2. Runs without exit hashes, including the
existing pilot B, can use read-only `eval.runner.reaudit` for diagnostics but
require a host executor rerun before regrading is possible.
